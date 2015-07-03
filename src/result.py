from typing import TypeVar, Any, Callable

T = TypeVar('T')
N = TypeVar('N', Any, None)

class Ok(object):
    """
    Result,
        from Rust.
    """

    def __init__(self, target: T) -> None:
        """
        >>> Ok(1)
        Ok<1>
        >>> Err('str')
        Err<'str'>
        """
        self.target = target

    def __repr__(self) -> str:
        return "{}<{!r}>".format(type(self).__name__, self.target)

    def unwrap(self) -> T:
        """
        >>> Ok(1).unwrap()
        1
        >>> Err(1).unwrap()
        1
        """
        return self.target

    def is_ok(self) -> bool:
        """
        >>> Ok(1).is_ok()
        True
        >>> Err(1).is_ok()
        False
        """
        return type(self) == Ok

    def is_err(self) -> bool:
        """
        >>> Err(1).is_err()
        True
        >>> Ok(1).is_err()
        False
        """
        return type(self) == Err

    def ok(self) -> N:
        """
        >>> Ok(1).ok()
        1
        >>> Err(1).ok()
        """
        return self.unwrap() if self.is_ok() else None

    def err(self) -> N:
        """
        >>> Err(1).err()
        1
        >>> Ok(1).err()
        """
        return self.unwrap() if self.is_err() else None

    def map(self, fn: Callable[[T], Any]) -> Any:
        """
        >>> Ok(1).map(lambda i: i+1)
        2
        >>> Err(1).map(lambda i: i+1)
        2
        """
        return fn(self.unwrap())

    def map_err(self, fn: Callable[[T], Any]) -> Any:
        """
        >>> Ok(1).map_err(lambda i: Err(i+1))
        Ok<1>
        >>> Err(1).map_err(lambda i: Err(i+1))
        Err<2>
        """
        return fn(self.unwrap()) if self.is_err() else self

    def and_then(self, fn: Callable[[T], Any]) -> Any:
        """
        >>> Ok(1).and_then(lambda i: Ok(i+1))
        Ok<2>
        >>> Err(1).and_then(lambda i: Ok(i+1))
        Err<1>
        """
        return fn(self.unwrap()) if self.is_ok() else self

class Err(Ok, Exception):
    """
    >>> try:
    ...     raise Err("err")
    ... except Err as e:
    ...     e
    Err<'err'>
    """
    pass

Result = TypeVar('Result', Ok, Err)
