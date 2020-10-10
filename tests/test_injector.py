from typing import List
from applipy_inject import Injector
from .common import Sub, Super


def test_bind_instance_unnamed():
    injector = Injector()

    injector.bind(str, '15')

    assert injector.get(str) == '15'


def test_bind_instance_named():
    injector = Injector()

    injector.bind(dict, {'b': 1})
    injector.bind(dict, {'a': 2}, name='foo')

    assert injector.get(dict, name='foo') == {'a': 2}


def test_bind_instance_subtype():
    injector = Injector()

    injector.bind(int, 5)
    injector.bind(dict, {'b': 1})
    injector.bind(str, 'foo')
    instance = Sub(5, {'b': 1}, 'foo')
    injector.bind(Super, instance)

    assert id(injector.get(Super)) == id(instance)


def test_bind_provider_unnamed():
    injector = Injector()

    def int_provider(s: str) -> int:
        return int(s)

    injector.bind(int_provider)
    injector.bind(str, '42')

    assert injector.get(int) == 42


def test_bind_provider_named():
    injector = Injector()

    def int_provider_a(s: str) -> int:
        return int(s) * 2

    def int_provider_b(s: str) -> int:
        return int(s)

    injector.bind(int_provider_a)
    injector.bind(int_provider_b, name='bar')
    injector.bind(str, '23')

    assert injector.get(int, name='bar') == 23


def test_bind_provider_singleton():
    injector = Injector()

    def int_provider_a() -> int:
        return dict(((1, 2), (3, 4)))

    injector.bind(int_provider_a, singleton=True)

    assert id(injector.get(int)) == id(injector.get(int))
    assert injector.get(int) == injector.get(int)


def test_bind_provider_not_singleton():
    injector = Injector()

    def int_provider_a() -> int:
        return dict(((1, 2), (3, 4)))

    injector.bind(int_provider_a, singleton=False)

    assert id(injector.get(int)) != id(injector.get(int))
    assert injector.get(int) == injector.get(int)


def test_bind_provider_subtype():
    injector = Injector()

    injector.bind(int, 5)
    injector.bind(dict, {'b': 1})
    injector.bind(str, 'foo')

    def sub_provider(a: int, b: dict, c: str) -> Sub:
        return Sub(a, b, c)

    injector.bind(Super, sub_provider)

    assert injector.get(Super) == Sub(5, {'b': 1}, 'foo')


def test_bind_type_unnamed():
    injector = Injector()

    injector.bind(Super)
    injector.bind(int, 5)
    injector.bind(dict, {'c': 7})

    assert injector.get(Super) == Super(5, {'c': 7})


def test_bind_type_named():
    injector = Injector()

    injector.bind(Super, Sub(1, {}, '2'))
    injector.bind(Super, name='z')
    injector.bind(int, 7)
    injector.bind(dict, {'k': 7})

    assert injector.get(Super, name='z') == Super(7, {'k': 7})


def test_bind_type_singleton():
    injector = Injector()

    injector.bind(Super, singleton=True)
    injector.bind(int, 7)
    injector.bind(dict, {'k': 7})

    assert id(injector.get(Super)) == id(injector.get(Super))
    assert injector.get(Super) == injector.get(Super)


def test_bind_type_not_singleton():
    injector = Injector()

    injector.bind(Super, singleton=False)
    injector.bind(int, 7)
    injector.bind(dict, {'k': 7})

    assert id(injector.get(Super)) != id(injector.get(Super))
    assert injector.get(Super) == injector.get(Super)


def test_get_all():
    injector = Injector()

    injector.bind(int, 1)
    injector.bind(int, 2)
    injector.bind(int, 3)
    injector.bind(int, 4)
    injector.bind(str, 'a', name='k')
    injector.bind(str, 'b')
    injector.bind(str, 'c', name='k')

    assert set(injector.get_all(int)) == set((1, 2, 3, 4))
    assert injector.get_all(str) == ['b']
    assert set(injector.get_all(str, name='k')) == set(('a', 'c'))
    assert injector.get_all(bool) == []


def test_collection_dependency():
    injector = Injector()

    injector.bind(int, 1)
    injector.bind(int, 2)
    injector.bind(int, 3)
    injector.bind(int, 4)

    def mysum(ints: List[int]) -> str:
        return ','.join(str(x) for x in sorted(ints))

    injector.bind(mysum)

    assert injector.get(str) == '1,2,3,4'
