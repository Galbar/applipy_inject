from typing import (
    Any,
    Dict,
)


class Super:

    def __init__(self, a: int, b: Dict[str, int]) -> None:
        self.a = a
        self.b = b

    def __eq__(self, o: Any) -> bool:
        if not isinstance(o, Super):
            return False

        return self.a == o.a and self.b == o.b

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(a={self.a}, b={self.b})'


class Sub(Super):

    def __init__(self, a: int, b: Dict[str, int], c: str) -> None:
        super().__init__(a, b)
        self.c = c

    def __eq__(self, o: Any) -> bool:
        if not super().__eq__(o):
            return False
        if not isinstance(o, Sub):
            return False

        return self.c == o.c

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(a={self.a}, b={self.b}, c={self.c})'
