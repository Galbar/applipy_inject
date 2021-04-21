from collections import defaultdict
from enum import Enum
from typing import (
    List,
    Union,
)


def with_names(provider, names):

    def wrapper(*args, **kwargs):
        return provider(*args, **kwargs)

    if not isinstance(names, dict):
        name = names
        names = defaultdict(lambda: name)

    if isinstance(provider, type):
        annotations = getattr(provider.__init__, '__annotations__', {}).copy()
        annotations['return'] = provider
    else:
        annotations = getattr(provider, '__annotations__', {})

    wrapper._named_deps = names
    wrapper.__annotations__ = annotations
    return wrapper


def named(names):
    def construct_wrapper(func):
        return with_names(func, names)

    return construct_wrapper


class DependencyType(str, Enum):
    Required = 'required'
    Optional = 'optional'
    Collection = 'collection'


class Dependency:

    def __init__(self, name, type_, varname, dep_type):
        self.name = name
        self.type_ = type_
        self.varname = varname
        self.dep_type = dep_type


class Provider:

    def __init__(self, callable_, dependencies):
        self.callable_ = callable_
        self.dependencies = dependencies

    def __repr__(self) -> str:
        return f'{self.__class__}[{self.callable_}]'


class Item:

    def __init__(self, name, provider, is_singleton, is_instanced, instance=None):
        self.name = name
        self.provider = provider
        self.is_singleton = is_singleton
        self.is_instanced = is_instanced
        self.instance = instance

    def instantiate(self, *args, **kwargs):
        if self.is_instanced:
            return
        instance = self.provider.callable_(*args, **kwargs)
        if self.is_singleton:
            self.is_instanced = True
            self.instance = instance
        return instance

    def __repr__(self) -> str:
        return f'{self.__class__}[{self.name}, {self.provider}]'


class Injector:

    def __init__(self):
        self.providers = defaultdict(set)

    def _dependency_is_collection(self, dep_type) -> bool:
        origin = getattr(dep_type, '__origin__', None)
        return origin is not None and (origin is list or origin is List)

    def _dependency_is_optional(self, dep_type) -> bool:
        origin = getattr(dep_type, '__origin__', None)
        if origin is not Union:
            return False
        args = getattr(dep_type, '__args__', ())
        if len(args) != 2:
            return False
        return type(None) in args

    def _get_dependency_type(self, type_):
        if self._dependency_is_collection(type_):
            return DependencyType.Collection
        elif self._dependency_is_optional(type_):
            return DependencyType.Optional
        else:
            return DependencyType.Required

    def _get_dependency_class(self, type_):
        if self._dependency_is_collection(type_):
            return type_.__args__[0]
        elif self._dependency_is_optional(type_):
            return next(t for t in type_.__args__ if not isinstance(t, type(None)))
        else:
            return type_

    def bind(self,
             type_,
             provider_or_instance=None,
             name=None,
             singleton=True):
        if provider_or_instance is None:
            if isinstance(type_, type):
                self.bind_type(type_, name=name, singleton=singleton)
            elif callable(type_) and isinstance(type_.__annotations__.get('return'), type):
                self.bind_provider(type_.__annotations__.get('return'), type_, name=name, singleton=singleton)
            else:
                raise TypeError('Cannot bind {}. Please be more explicit'.format(type_))
        elif self._is_provider(provider_or_instance, type_):
            self.bind_provider(type_,
                               provider_or_instance,
                               name=name,
                               singleton=singleton)
        else:
            self.bind_instance(type_, provider_or_instance, name=name)

    def _is_provider(self, provider_or_instance, type_) -> bool:
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
                isinstance(provider_or_instance, type)
                and
                issubclass(provider_or_instance, type_)
            )
            or
            (
                callable(provider_or_instance)
                and
                issubclass(
                    provider_or_instance.__annotations__.get('return'),
                    type_
                )
            )
        )

    def bind_provider(self, types, provider, name=None, singleton=True):
        if isinstance(provider, type):
            func = provider.__init__
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

        has_names = hasattr(func, '_named_deps')
        if has_names and isinstance(func._named_deps, defaultdict):
            named_deps = func._named_deps
        else:
            named_deps = defaultdict(lambda: None)
            if has_names:
                named_deps.update(func._named_deps)
        dependencies = {Dependency(named_deps[varname],
                                   self._get_dependency_class(t),
                                   varname,
                                   self._get_dependency_type(t))
                        for varname, t in annotations.items()}

        item = Item(name, Provider(provider, dependencies), singleton, False)

        for type_ in types:
            self.providers[name, type_].add(item)

    def bind_type(self, type_, name=None, singleton=True):
        self.bind_provider(type_, type_, name=name, singleton=singleton)

    def bind_instance(self, types, instance, name=None):
        item = Item(name, Provider(lambda: instance, {}), True, True, instance)

        if not isinstance(types, (tuple, list)):
            types = (types,)
        for type_ in types:
            self.providers[name, type_].add(item)

    def get_all(self, type_, name=None, _requested=None, _max=None):
        requested = _requested or set()
        request_key = (name, type_)
        if request_key in requested:
            raise Exception(f'There is a dependency cycle for type `{type_.__name__}` with name `{name}`')
        requested.add(request_key)

        items = self.providers[name, type_]

        instances_left = len(items) if _max is None else _max

        instances = []

        for item in items:
            is_singleton = item.is_singleton

            if is_singleton and item.is_instanced:
                instance = item.instance
            else:
                dependencies = {}
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

    def get_optional(self, type_, name=None, _requested=None):
        found = self.get_all(type_, name=name, _requested=_requested, _max=1)
        if found:
            return found[0]
        return None

    def get(self, type_, name=None, _requested=None):
        instance = self.get_optional(type_, name=name, _requested=_requested)
        if instance is None:
            raise ValueError(f'Could not get instance of type `{type_.__name__}` with name `{name}`')
        return instance
