from applipy_inject import Injector, with_names
from .common import Super


def provider(a: int, b: dict) -> Super:
    return Super(a, b)


def test_with_names_str_class():
    injector = Injector()

    injector.bind(int, 0)
    injector.bind(int, 5, name='foo')
    injector.bind(dict, {'z': 0})
    injector.bind(dict, {'l': 7}, name='foo')
    injector.bind(with_names(Super, 'foo'))

    assert injector.get(Super) == Super(5, {'l': 7})


def test_with_names_dict_class():
    injector = Injector()

    injector.bind(int, 0)
    injector.bind(int, 5, name='bar')
    injector.bind(dict, {'z': 0})
    injector.bind(dict, {'l': 7}, name='bar')
    injector.bind(with_names(Super, {'b': 'bar'}))

    assert injector.get(Super) == Super(0, {'l': 7})


def test_named_str_provider():
    injector = Injector()

    injector.bind(int, 0)
    injector.bind(int, 5, name='foo')
    injector.bind(dict, {'z': 0})
    injector.bind(dict, {'l': 7}, name='foo')
    injector.bind(with_names(provider, 'foo'))

    assert injector.get(Super) == Super(5, {'l': 7})


def test_named_dict_provider():
    injector = Injector()

    injector.bind(int, 0)
    injector.bind(int, 5, name='bar')
    injector.bind(dict, {'z': 0})
    injector.bind(dict, {'l': 7}, name='bar')
    injector.bind(with_names(provider, {'b': 'bar'}))

    assert injector.get(Super) == Super(0, {'l': 7})
