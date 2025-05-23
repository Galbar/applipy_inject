[![pipeline status](https://gitlab.com/applipy/applipy_inject/badges/master/pipeline.svg)](https://gitlab.com/applipy/applipy_inject/-/pipelines?scope=branches&ref=master)
[![coverage report](https://gitlab.com/applipy/applipy_inject/badges/master/coverage.svg)](https://gitlab.com/applipy/applipy_inject/-/graphs/master/charts)
[![PyPI Status](https://img.shields.io/pypi/status/applipy-inject.svg)](https://pypi.org/project/applipy-inject/)
[![PyPI Version](https://img.shields.io/pypi/v/applipy-inject.svg)](https://pypi.org/project/applipy-inject/)
[![PyPI Python](https://img.shields.io/pypi/pyversions/applipy-inject.svg)](https://pypi.org/project/applipy-inject/)
[![PyPI License](https://img.shields.io/pypi/l/applipy-inject.svg)](https://pypi.org/project/applipy-inject/)
[![PyPI Format](https://img.shields.io/pypi/format/applipy-inject.svg)](https://pypi.org/project/applipy-inject/)

# Applipy Inject

    pip install applipy_inject

Library that provides a dependency injector that works with type hinting.

## Basic usage

```python
from applipy_inject import Injector

injector = Injector()

# bind dictionary instance
injector.bind(dict, {'v': 143, 'k': 'bar'})

class A:
    def __init__(self, v: int):
        self.v = v

class B(A):
    def __init__(self, d: dict):
        super().__init__(d['v'])
        self.d = d

# bind subtype B to type A
injector.bind(A, B)

class C:
    def __init__(self, a: A):
        self.a = a

# bind type C
injector.bind(C)

# get an instace of type C
c = injector.get(C)

# the instance is initialized correctly, resolving the dependecy chain
print(c.a.v)
```
Output:
```
143
```

### bind(...)

The `bind()` function lets bind an object to a type. The meaning on the binding
depends on the type of the object. In general the object can be one of:
 - instance: an instance of a type
 - type: a type
 - provider: a callable object that has type annotations for its arguments and
   a return type annotation.

The bind function can be used in multiple ways:

**bind(type, instance)**

Bind an instance to a type. The instance must be an instance of the type or of
a subtype of the type.

```python
injector.bind(int, 5)
```

**bind((typeA, typeB, ...), instance)**

Bind an instance to multiple types. The instance must be an instance of all the
types or of a subtype of all the types.

```python
injector.bind((str, object), 'hello')
```

**bind(type)**

The type is bound as a "provider" of its own type and dependecy annotations are
taken from the `__init__` function.

```python
injector.bind(A)
```

**bind(type, subtype)**

Similar to `bind(type)` but subtype is bound to the specified type.

```python
injector.bind(A, B)
```

**bind((typeA, typeB, ...), subtype)**

Similar to `bind(type, subtype)` but subtype is bound to the specified types.

```python
injector.bind((A, B), B)
# or
injector.bind((A, B), C)
```

**bind(provider)**

The provider will be bound to the type it returns (as per the type annotation).

```python
def provide_A(s: str) -> A:
    return A(int(s))

injector.bind(provide_A)
```

**bind(type, provider)**

Similar to `bind(provider)` but the provider is bound to the specified type.
The annotated return type of the provider must be a subtype of the specified
type.

```python
def provide_B(v: int, k: str) -> B:
    return B({'v': v, 'k': k})

injector.bind(A, provide_B)
```

**bind((typeA, typeB, ...), provider)**

Similar to `bind(type, provider)` but the provider is bound to all the
specified types. The annotated return type of the provider must be a subtype
of all the specified types.

```python
def provide_B(v: int, k: str) -> B:
    return B({'v': v, 'k': k})

injector.bind((A, B), provide_B)
```

**Common optional parameters:**
 - `name`: defaults to `None`. Lets the user give a name to the binding. This
   allows to make multiple bindings to the same type and be able to select
   which one you want to get by using the name.

 - `singleton`: defaults to `True`. Define whether the injector should
   instantiate or call the provider only once and inject always the same
   instance or return a new result every time. It does not applipy to bound
   instances.

```python
injector.bind(provide_A, name='foo', singleton=False)
```

### get(...)

Get an instance registered to a given type.

Similar to `bind()`, there is an optional `name` parameter that tells the
injector the name of the instance to get for that type.

```
injector.get(A, name='foo')
```

### get_all(...)

The `Injector` allows to bind multiple objects to the same type and name.
`get_all()` retrieves all instances for a given type and name combination as a
list, instead of just one as `get()` does.

Similar to `bind()`, there is an optional `name` parameter that tells the
injector the name of the instance to get for that type.

```
injector.get_all(A, name='foo')
```

## Named dependencies

Dependencies can be given names so that different providers can depend on
different instances of the same type. This can be achieved by annotating the
dependency type with the dependency name:

```python
from typing import Annotated
from applipy_inject import name


def provide_A(s: Annotated[str, name('foo_num')]) -> A:
    return A(int(s))


injector.bind(str, '13', name='foo_num')
injector.bind(provide_A)
```

## Utility functions

### with_names(provider, names)

Give names to the arguments of an existing provider or class. The injector will
use this to set the value for `name` with doing `get()`.

`names` can be:
 - `dict`, where the keys are the names of the arguments and the values are the
   names for their type.
 - `str`, all arguments will be named with the value

```python
injector.bind(with_names(provide_B, {'k': 'name_for_k'}))
```
> Note that `v` won't have a name

```python
injector.bind(with_names(provide_B, 'name_for_all'))
```
> Both `v` and `k` will have name `name_for_all`

It can also be used on classes:
```python
injector.bind(with_names(C, 'app'))
```

### named(...)

Similar to `with_names()` but it is a decorator that is used when defining a
provider or class `__init__`.

```python

class Z:
    @named({'a': 'conf'})
    def __init__(self, a: dict, b: str):
        ...


@named('foo')
def provide_int(x: int, b: str) -> int:
    ...
```

This is equivalent to using `typing.Annotated` as follows:

```python
from typing import Annotated
from applipy_inject import name

class Z:
    def __init__(self, a: Annotated[dict, name('conf')], b: str):
        ...


def provide_int(x: Annotated[int, name('foo')], b: Annotated[str, name('foo')]) -> int:
    ...
```
