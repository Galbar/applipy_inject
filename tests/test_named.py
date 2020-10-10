from applipy_inject import Injector, named
from .common import Super


def test_named_str_class():
    class A:
        @named('foo')
        def __init__(self, a: int, b: str):
            self.a = a
            self.b = b

        def __eq__(self, o):
            return self.a == o.a and self.b == o.b

        def __repr__(self):
            return f'{self.__class__.__name__}(a={self.a}, b={self.b})'

    injector = Injector()

    injector.bind(int, 0)
    injector.bind(int, 5, name='foo')
    injector.bind(str, 'z')
    injector.bind(str, 'l', name='foo')
    injector.bind(A)

    assert injector.get(A) == A(5, 'l')


def test_named_dict_class():
    class A:
        @named({'b': 'bar'})
        def __init__(self, a: int, b: str):
            self.a = a
            self.b = b

        def __eq__(self, o):
            return self.a == o.a and self.b == o.b

        def __repr__(self):
            return f'{self.__class__.__name__}(a={self.a}, b={self.b})'

    injector = Injector()

    injector.bind(int, 0)
    injector.bind(int, 5, name='bar')
    injector.bind(str, 'z')
    injector.bind(str, 'l', name='bar')
    injector.bind(A)

    assert injector.get(A) == A(0, 'l')


def test_named_str_provider():
    @named('foo')
    def provider(a: int, b: dict) -> Super:
        return Super(a, b)

    injector = Injector()

    injector.bind(int, 0)
    injector.bind(int, 5, name='foo')
    injector.bind(dict, {'z': 2})
    injector.bind(dict, {'l': 1}, name='foo')
    injector.bind(provider)

    assert injector.get(Super) == Super(5, {'l': 1})


def test_named_dict_provider():
    @named({'b': 'bar'})
    def provider(a: int, b: dict) -> Super:
        return Super(a, b)

    injector = Injector()

    injector.bind(int, 0)
    injector.bind(int, 5, name='bar')
    injector.bind(dict, {'z': 2})
    injector.bind(dict, {'l': 1}, name='bar')
    injector.bind(provider)

    assert injector.get(Super) == Super(0, {'l': 1})
