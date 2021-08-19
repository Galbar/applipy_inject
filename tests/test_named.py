from typing import (
    Any,
    Dict,
)
from applipy_inject import Injector, named
from .common import Super


def test_named_str_class() -> None:
    class A:
        @named('foo')
        def __init__(self, a: int, b: str) -> None:
            self.a = a
            self.b = b

        def __eq__(self, o: Any) -> bool:
            if not isinstance(o, A):
                return False
            return self.a == o.a and self.b == o.b

        def __repr__(self) -> str:
            return f'{self.__class__.__name__}(a={self.a}, b={self.b})'

    injector = Injector()

    injector.bind(int, 0)
    injector.bind(int, 5, name='foo')
    injector.bind(str, 'z')
    injector.bind(str, 'l', name='foo')
    injector.bind(A)

    assert injector.get(A) == A(5, 'l')


def test_named_dict_class() -> None:
    class A:
        @named({'b': 'bar'})
        def __init__(self, a: int, b: str) -> None:
            self.a = a
            self.b = b

        def __eq__(self, o: Any) -> bool:
            if not isinstance(o, A):
                return False
            return self.a == o.a and self.b == o.b

        def __repr__(self) -> str:
            return f'{self.__class__.__name__}(a={self.a}, b={self.b})'

    injector = Injector()

    injector.bind(int, 0)
    injector.bind(int, 5, name='bar')
    injector.bind(str, 'z')
    injector.bind(str, 'l', name='bar')
    injector.bind(A)

    assert injector.get(A) == A(0, 'l')


def test_named_str_provider() -> None:
    @named('foo')
    def provider(a: int, b: Dict[str, int]) -> Super:
        return Super(a, b)

    injector = Injector()

    injector.bind(int, 0)
    injector.bind(int, 5, name='foo')
    injector.bind(Dict[str, int], {'z': 2})
    injector.bind(Dict[str, int], {'l': 1}, name='foo')
    injector.bind(provider)

    assert injector.get(Super) == Super(5, {'l': 1})


def test_named_dict_provider() -> None:
    @named({'b': 'bar'})
    def provider(a: int, b: Dict[str, int]) -> Super:
        return Super(a, b)

    injector = Injector()

    injector.bind(int, 0)
    injector.bind(int, 5, name='bar')
    injector.bind(Dict[str, int], {'z': 2})
    injector.bind(Dict[str, int], {'l': 1}, name='bar')
    injector.bind(provider)

    assert injector.get(Super) == Super(0, {'l': 1})
