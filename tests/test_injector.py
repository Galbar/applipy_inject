from typing import (
    Dict,
    List,
    Optional,
)

from applipy_inject import Injector

from .common import Sub, Super


def test_bind_instance_unnamed() -> None:
    injector = Injector()

    injector.bind(str, '15')

    assert injector.get(str) == '15'


def test_bind_instance_named() -> None:
    injector = Injector()

    injector.bind(dict, {'b': 1})
    injector.bind(dict, {'a': 2}, name='foo')

    assert injector.get(dict, name='foo') == {'a': 2}


def test_bind_instance_subtype() -> None:
    injector = Injector()

    injector.bind(int, 5)
    injector.bind(Dict[str, int], {'b': 1})
    injector.bind(str, 'foo')
    instance = Sub(5, {'b': 1}, 'foo')
    injector.bind(Super, instance)

    assert id(injector.get(Super)) == id(instance)


def test_bind_provider_unnamed() -> None:
    injector = Injector()

    def int_provider(s: str) -> int:
        return int(s)

    injector.bind(int_provider)
    injector.bind(str, '42')

    assert injector.get(int) == 42


def test_bind_provider_named() -> None:
    injector = Injector()

    def str_provider(s: str) -> int:
        return int(s) * 2

    def int_provider_b(s: str) -> int:
        return int(s)

    injector.bind(str_provider)
    injector.bind(int_provider_b, name='bar')
    injector.bind(str, '23')

    assert injector.get(int, name='bar') == 23


def test_bind_provider_singleton() -> None:
    injector = Injector()

    def dict_provider() -> Dict[int, int]:
        return dict(((1, 2), (3, 4)))

    injector.bind(dict_provider, singleton=True)

    assert injector.get(Dict[int, int]) == {1: 2, 3: 4}
    assert id(injector.get(Dict[int, int])) == id(injector.get(Dict[int, int]))
    assert injector.get(Dict[int, int]) == injector.get(Dict[int, int])


def test_bind_provider_not_singleton() -> None:
    injector = Injector()

    def dict_provider() -> Dict[int, int]:
        return dict(((1, 2), (3, 4)))

    injector.bind(dict_provider, singleton=False)

    assert injector.get(Dict[int, int]) == {1: 2, 3: 4}
    assert id(injector.get(Dict[int, int])) != id(injector.get(Dict[int, int]))
    assert injector.get(Dict[int, int]) == injector.get(Dict[int, int])


def test_bind_provider_subtype() -> None:
    injector = Injector()

    injector.bind(int, 5)
    injector.bind(Dict[str, int], {'b': 1})
    injector.bind(str, 'foo')

    def sub_provider(a: int, b: Dict[str, int], c: str) -> Sub:
        return Sub(a, b, c)

    injector.bind(Super, sub_provider)

    assert injector.get(Super) == Sub(5, {'b': 1}, 'foo')


def test_bind_type_unnamed() -> None:
    injector = Injector()

    injector.bind(Super)
    injector.bind(int, 5)
    injector.bind(Dict[str, int], {'c': 7})

    assert injector.get(Super) == Super(5, {'c': 7})


def test_bind_type_named() -> None:
    injector = Injector()

    injector.bind(Super, Sub(1, {}, '2'))
    injector.bind(Super, name='z')
    injector.bind(int, 7)
    injector.bind(Dict[str, int], {'k': 7})

    assert injector.get(Super, name='z') == Super(7, {'k': 7})


def test_bind_type_singleton() -> None:
    injector = Injector()

    injector.bind(Super, singleton=True)
    injector.bind(int, 7)
    injector.bind(Dict[str, int], {'k': 7})

    assert id(injector.get(Super)) == id(injector.get(Super))
    assert injector.get(Super) == injector.get(Super)


def test_bind_type_not_singleton() -> None:
    injector = Injector()

    injector.bind(Super, singleton=False)
    injector.bind(int, 7)
    injector.bind(Dict[str, int], {'k': 7})

    assert id(injector.get(Super)) != id(injector.get(Super))
    assert injector.get(Super) == injector.get(Super)


def test_get_all() -> None:
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


def test_collection_dependency() -> None:
    injector = Injector()

    injector.bind(int, 1)
    injector.bind(int, 2)
    injector.bind(int, 3)
    injector.bind(int, 4)

    def mysum(ints: List[int]) -> str:
        return ','.join(str(x) for x in sorted(ints))

    injector.bind(mysum)

    assert injector.get(str) == '1,2,3,4'


def test_optional_dependency_present() -> None:
    injector = Injector()

    injector.bind(int, 1)

    def mysum(maybe_int: Optional[int]) -> str:
        return str(maybe_int)

    injector.bind(mysum)

    assert injector.get(str) == '1'


def test_optional_dependency_absent() -> None:
    injector = Injector()

    def mysum(maybe_int: Optional[int]) -> str:
        return str(maybe_int)

    injector.bind(mysum)

    assert injector.get(str) == 'None'


def test_bind_instance_to_multiple_types_tuple() -> None:
    injector = Injector()

    injector.bind((str, object), 'many-things')

    assert injector.get(str) == 'many-things'
    assert injector.get(object) == 'many-things'
    assert injector.get(str) is injector.get(object)


def test_bind_instance_to_multiple_types_list() -> None:
    injector = Injector()

    injector.bind([str, object], 'many-things')

    assert injector.get(str) == 'many-things'
    assert injector.get(object) == 'many-things'
    assert injector.get(str) is injector.get(object)


def test_bind_provider_to_multiple_types_tuple() -> None:
    injector = Injector()

    injector.bind((Super, Sub), Sub, singleton=True)
    injector.bind(int, 7)
    injector.bind(Dict[str, int], {'k': 7})
    injector.bind(str, 'c')

    assert id(injector.get(Super)) == id(injector.get(Super))
    assert injector.get(Super) == injector.get(Super)
    assert id(injector.get(Sub)) == id(injector.get(Sub))
    assert injector.get(Sub) == injector.get(Sub)
    assert id(injector.get(Super)) == id(injector.get(Sub))
    assert injector.get(Super) == injector.get(Sub)


def test_bind_provider_to_multiple_types_list() -> None:
    injector = Injector()

    injector.bind([Super, Sub], Sub, singleton=True)
    injector.bind(int, 7)
    injector.bind(Dict[str, int], {'k': 7})
    injector.bind(str, 'c')

    assert id(injector.get(Super)) == id(injector.get(Super))
    assert injector.get(Super) == injector.get(Super)
    assert id(injector.get(Sub)) == id(injector.get(Sub))
    assert injector.get(Sub) == injector.get(Sub)
    assert id(injector.get(Super)) == id(injector.get(Sub))
    assert injector.get(Super) == injector.get(Sub)
