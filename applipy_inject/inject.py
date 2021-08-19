from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)
from collections import defaultdict
from enum import Enum


T = TypeVar('T')
T_Co = TypeVar('T_Co', covariant=True)


def with_names(provider: Callable[..., T], names: Union[Dict[str, str], str]) -> Callable[..., T]:

    def wrapper(*args: Any, **kwargs: Any) -> T:
        return provider(*args, **kwargs)

    if not isinstance(names, dict):
        name = names
        names = defaultdict(lambda: name)

    if isinstance(provider, type):
        init = getattr(provider, '__init__')
        if init:
            annotations = getattr(init, '__annotations__', {}).copy()
            annotations['return'] = provider
    else:
        annotations = getattr(provider, '__annotations__', {})

    setattr(wrapper, '_named_deps', names)
    setattr(wrapper, '__annotations__', annotations)
    return wrapper


def named(names: Union[Dict[str, str], str]) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def construct_wrapper(func: Callable[..., T]) -> Callable[..., T]:
        return with_names(func, names)

    return construct_wrapper


class DependencyType(str, Enum):
    Required = 'required'
    Optional = 'optional'
    Collection = 'collection'


class Dependency:

    name: Optional[str]
    type_: type
    varname: str
    dep_type: DependencyType

    def __init__(self, name: Optional[str], type_: type, varname: str, dep_type: DependencyType) -> None:
        self.name = name
        self.type_ = type_
        self.varname = varname
        self.dep_type = dep_type


class Provider(Generic[T_Co]):

    dependencies: Iterable[Dependency]

    def __init__(self, callable_: Callable[..., T_Co], dependencies: Iterable[Dependency]) -> None:
        self.callable_: Callable[..., T_Co] = callable_
        self.dependencies = dependencies

    def __repr__(self) -> str:
        return f'{self.__class__}[{self.callable_}]'


class Item(Generic[T_Co]):

    name: Optional[str]
    provider: Provider[T_Co]
    is_singleton: bool
    instance: Optional[T_Co]

    def __init__(self,
                 name: Optional[str],
                 provider: Provider[T_Co],
                 is_singleton: bool,
                 instance: Optional[T_Co] = None) -> None:
        self.name = name
        self.provider = provider
        self.is_singleton = is_singleton
        self.instance = instance

    def instantiate(self, *args: Any, **kwargs: Any) -> T_Co:
        instance = self.provider.callable_(*args, **kwargs)
        if self.is_singleton:
            self.instance = instance
        return instance

    def __repr__(self) -> str:
        return f'{self.__class__}[{self.name}, {self.provider}]'


class Injector:

    providers: Dict[Tuple[Optional[str], type], Set[Item[object]]]

    def __init__(self) -> None:
        self.providers = defaultdict(set)

    def _dependency_is_collection(self, dep_type: type) -> bool:
        origin = getattr(dep_type, '__origin__', None)
        return origin is not None and (origin is list or origin is List)

    def _dependency_is_optional(self, dep_type: type) -> bool:
        origin = getattr(dep_type, '__origin__', None)
        if origin is not Union:
            return False
        args = getattr(dep_type, '__args__', ())
        if len(args) != 2:
            return False
        return type(None) in args

    def _get_dependency_type(self, type_: type) -> DependencyType:
        if self._dependency_is_collection(type_):
            return DependencyType.Collection
        elif self._dependency_is_optional(type_):
            return DependencyType.Optional
        else:
            return DependencyType.Required

    def _get_dependency_class(self, type_: type) -> type:
        if self._dependency_is_collection(type_):
            return cast(type, getattr(type_, '__args__')[0])
        elif self._dependency_is_optional(type_):
            return next(cast(type, t) for t in getattr(type_, '__args__') if not isinstance(t, type(None)))
        else:
            return type_

    @overload
    def bind(self, type_: Type[T],
             provider_or_instance: None = None, name: Optional[str] = None, singleton: bool = False) -> None:
        ...

    @overload
    def bind(self, type_: Callable[..., T],
             provider_or_instance: None = None, name: Optional[str] = None, singleton: bool = False) -> None:
        ...

    @overload
    def bind(self, type_: Type[T], provider_or_instance: Callable[..., T],
             name: Optional[str] = None, singleton: bool = False) -> None:
        ...

    @overload
    def bind(self, type_: Tuple[type, ...], provider_or_instance: Callable[..., object],
             name: Optional[str] = None, singleton: bool = False) -> None:
        ...

    @overload
    def bind(self, type_: List[type], provider_or_instance: Callable[..., object],
             name: Optional[str] = None, singleton: bool = False) -> None:
        ...

    @overload
    def bind(self, type_: Type[T], provider_or_instance: T,
             name: Optional[str] = None, singleton: bool = False) -> None:
        ...

    @overload
    def bind(self, type_: Tuple[type, ...], provider_or_instance: object,
             name: Optional[str] = None, singleton: bool = False) -> None:
        ...

    @overload
    def bind(self, type_: List[type], provider_or_instance: object,
             name: Optional[str] = None, singleton: bool = False) -> None:
        ...

    def bind(self,
             type_: Union[Type[T], Tuple[type, ...], List[type], Callable[..., T]],
             provider_or_instance: Optional[Union[T, Callable[..., object], object]] = None,
             name: Optional[str] = None,
             singleton: bool = True) -> None:
        if provider_or_instance is None:
            if isinstance(type_, type):
                self.bind_type(type_, name=name, singleton=singleton)
            elif callable(type_) and isinstance(type_.__annotations__.get('return'), type):
                self.bind_provider(type_.__annotations__['return'], type_, name=name, singleton=singleton)
            else:
                raise TypeError('Cannot bind {}. Please be more explicit'.format(type_))
        elif self._is_provider(provider_or_instance, type_):
            self.bind_provider(cast(Union[Type[T], Tuple[type, ...], List[type]], type_),
                               cast(Callable[..., T], provider_or_instance),
                               name=name,
                               singleton=singleton)
        else:
            self.bind_instance(cast(Union[Type[T], Tuple[Type[T], ...], List[Type[T]]], type_),
                               cast(T, provider_or_instance),
                               name=name)

    def _is_provider(self,
                     provider_or_instance: Union[T, Callable[..., T]],
                     type_: Union[Type[T], Callable[..., T], Tuple[Type[T], ...], List[Type[T]]]) -> bool:
        return (
            (
                isinstance(type_, (tuple, list))
                and
                all(isinstance(t, type) for t in type_)
                and
                all(self._is_provider(provider_or_instance, t) for t in type_)
            )
            or
            (
                isinstance(type_, type)
                and
                isinstance(provider_or_instance, type)
                and
                issubclass(provider_or_instance, type_)
            )
            or
            (
                isinstance(type_, type)
                and
                callable(provider_or_instance)
                and
                issubclass(
                    provider_or_instance.__annotations__['return'],
                    type_
                )
            )
        )

    def bind_provider(self,
                      types: Union[Type[T], Tuple[type, ...], List[type]],
                      provider: Callable[..., T],
                      name: Optional[str] = None,
                      singleton: bool = True) -> None:
        func: Callable[..., T]
        if isinstance(provider, type):
            func = cast(Callable[..., T], getattr(provider, '__init__'))
        else:
            func = provider

        if not isinstance(types, (tuple, list)):
            types = (types,)

        if hasattr(func, '__annotations__'):
            annotations = func.__annotations__.copy()
            if 'return' in annotations:
                del annotations['return']
        else:
            annotations = {}

        named_deps_raw = getattr(func, '_named_deps', None)
        has_names = named_deps_raw is not None
        if has_names and isinstance(named_deps_raw, defaultdict):
            named_deps = named_deps_raw
        else:
            named_deps = defaultdict(lambda: None)
            if has_names:
                named_deps.update(named_deps_raw)
        dependencies = {Dependency(named_deps[varname],
                                   self._get_dependency_class(t),
                                   varname,
                                   self._get_dependency_type(t))
                        for varname, t in annotations.items()}

        item = Item[T](name, Provider(provider, dependencies), singleton)

        for type_ in types:
            self.providers[name, type_].add(item)

    def bind_type(self,
                  type_: type,
                  name: Optional[str] = None,
                  singleton: bool = True) -> None:
        self.bind_provider(type_, type_, name=name, singleton=singleton)

    def bind_instance(self,
                      types: Union[Type[T], Tuple[Type[T], ...], List[Type[T]]],
                      instance: T,
                      name: Optional[str] = None) -> None:
        item = Item[T](name, Provider(lambda: instance, ()), True, instance=instance)

        if not isinstance(types, (tuple, list)):
            types = (types,)
        for type_ in types:
            self.providers[name, type_].add(item)

    def get_all(self,
                type_: Type[T],
                name: Optional[str] = None,
                _requested: Optional[Set[Tuple[Optional[str], type]]] = None,
                _max: Optional[int] = None) -> List[T]:
        requested = _requested or set()
        request_key = (name, type_)
        if request_key in requested:
            raise Exception(f'There is a dependency cycle for type `{type_.__name__}` with name `{name}`')
        requested.add(request_key)

        items = cast(Set[Item[T]], self.providers[name, type_])

        instances_left = len(items) if _max is None else _max

        instances: List[T] = []

        for item in items:
            if item.instance is not None:
                instance = item.instance
            else:
                dependencies: Dict[str, Union[List[object], Optional[object], object]] = {}
                for dependency in item.provider.dependencies:
                    if dependency.dep_type == DependencyType.Collection:
                        dependencies[dependency.varname] = self.get_all(dependency.type_,
                                                                        name=dependency.name,
                                                                        _requested=requested)
                    elif dependency.dep_type == DependencyType.Optional:
                        dependencies[dependency.varname] = self.get_optional(dependency.type_,
                                                                             name=dependency.name,
                                                                             _requested=requested)
                    else:
                        dependencies[dependency.varname] = self.get(dependency.type_,
                                                                    name=dependency.name,
                                                                    _requested=requested)
                try:
                    instance = item.instantiate(**dependencies)
                except TypeError:
                    raise Exception(
                        f'Error when calling provider `{item.provider.callable_}` for type `{type_}` with name `{name}`'
                    )

            instances.append(instance)

            instances_left -= 1
            if instances_left == 0:
                break

        requested.remove(request_key)
        return instances

    def get_optional(self,
                     type_: Type[T],
                     name: Optional[str] = None,
                     _requested: Optional[Set[Tuple[Optional[str], type]]] = None) -> Optional[T]:
        found = self.get_all(type_, name=name, _requested=_requested, _max=1)
        if found:
            return found[0]
        return None

    def get(self,
            type_: Type[T],
            name: Optional[str] = None,
            _requested: Optional[Set[Tuple[Optional[str], type]]] = None) -> T:
        instance = self.get_optional(type_, name=name, _requested=_requested)
        if instance is None:
            raise ValueError(f'Could not get instance of type `{type_.__name__}` with name `{name}`')
        return instance
