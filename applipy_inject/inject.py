from typing import List
from collections import defaultdict


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


class Dependency:

    def __init__(self, name, type_, varname, is_collection):
        self.name = name
        self.type_ = type_
        self.varname = varname
        self.is_collection = is_collection


class Provider:

    def __init__(self, callable_, dependencies):
        self.callable_ = callable_
        self.dependencies = dependencies

    def __repr__(self) -> str:
        return f'{self.__class__}[{self.callable_}]'


class Item:

    def __init__(self, name, type_, provider, is_singleton):
        self.name = name
        self.type_ = type_
        self.provider = provider
        self.is_singleton = is_singleton

    def __repr__(self) -> str:
        return f'{self.__class__}[{self.name}, {self.provider}]'


class InstancedItem(Item):

    def __init__(self, name, type_, provider, is_singleton, instance):
        super().__init__(name, type_, provider, is_singleton)
        self.instance = instance


class Injector:

    def __init__(self):
        self.providers = defaultdict(set)

    def _dependency_is_collection(self, dep_type) -> bool:
        origin = getattr(dep_type, '__origin__', None)
        return origin is not None and (origin is list or origin is List)

    def _get_dependency_type(self, type_):
        if self._dependency_is_collection(type_):
            return type_.__args__[0]
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

    def bind_provider(self, type_, provider, name=None, singleton=True):
        if isinstance(provider, type):
            func = provider.__init__
        else:
            func = provider

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
                                   self._get_dependency_type(type_),
                                   varname,
                                   self._dependency_is_collection(type_))
                        for varname, type_ in annotations.items()}

        item = Item(name, type_, Provider(provider, dependencies), singleton)

        self.providers[name, type_].add(item)

    def bind_type(self, type_, name=None, singleton=True):
        self.bind_provider(type_, type_, name=name, singleton=singleton)

    def bind_instance(self, type_, instance, name=None):
        item = InstancedItem(name, type_, Provider(lambda: instance, {}), True, instance)
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

        items_instantiated = []

        for item in items:
            is_singleton = item.is_singleton

            if is_singleton and isinstance(item, InstancedItem):
                instance = item.instance
            else:
                dependencies = {}
                for dependency in item.provider.dependencies:
                    if dependency.is_collection:
                        dependencies[dependency.varname] = self.get_all(dependency.type_,
                                                                        name=dependency.name,
                                                                        _requested=requested)
                    else:
                        dependencies[dependency.varname] = self.get(dependency.type_,
                                                                    name=dependency.name,
                                                                    _requested=requested)
                try:
                    instance = item.provider.callable_(**dependencies)
                except TypeError:
                    raise Exception(
                        f'Error when calling provider `{item.provider.callable_}` for type `{type_}` with name `{name}`'
                    )

            if is_singleton:
                instanced_item = InstancedItem(item.name, item.type_, item.provider, is_singleton, instance)
                items_instantiated.append((item, instanced_item))

            instances.append(instance)

            instances_left -= 1
            if instances_left == 0:
                break

        for old, new in items_instantiated:
            items.remove(old)
            items.add(new)

        requested.remove(request_key)
        return instances

    def get(self, type_, name=None, _requested=None):
        try:
            return self.get_all(type_, name=name, _requested=_requested, _max=1)[0]
        except IndexError:
            raise Exception(f'Could not get instance of type `{type_.__name__}` with name `{name}`')
