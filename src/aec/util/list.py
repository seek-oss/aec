from typing import List, TypeVar, Union

E = TypeVar("E")
T = TypeVar("T")


def first_or_else(li: List[E], default: T) -> Union[E, T]:
    return li[0] if len(li) > 0 else default
