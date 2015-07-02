from typing import TypeVar, Any

T = TypeVar('T')
N = TypeVar('N', Any, None)

class Ok(object):
    """
    Result Ok,
        from Rust.
    """

    def __init__(self, target: T) -> None:
        '''
        >>> Ok(1)
        Ok<1>
        >>> Err('str')
        Err<'str'>
        '''
        self.target = target

    def __repr__(self) -> str:
        return "{}<{}>".format(type(self).__name__, repr(self.target))

    def unwrap(self) -> T:
        '''
        >>> Ok(1).unwrap()
        1
        '''
        return self.target

    def unwrap_or(self, target) -> T:
        '''
        >>> Ok(1).unwrap_or(2)
        1
        >>> Err(1).unwrap_or(2)
        2
        '''
        return self.unwrap() if self.is_ok() else target

    def is_ok(self) -> bool:
        '''
        >>> Ok(1).is_ok()
        True
        >>> Err(1).is_ok()
        False
        '''
        return type(self) == Ok

    def is_err(self) -> bool:
        '''
        >>> Err(1).is_err()
        True
        >>> Ok(1).is_err()
        False
        '''
        return type(self) == Err

    def ok(self) -> N:
        '''
        >>> Ok(1).ok()
        1
        >>> Err(1).ok()
        '''
        return self.unwrap() if self.is_ok() else None

    def err(self) -> N:
        '''
        >>> Err(1).err()
        1
        >>> Ok(1).err()
        '''
        return self.unwrap() if self.is_err() else None

    def map(self, fn) -> Any:
        '''
        >>> Ok(1).map(lambda i: i+1)
        2
        >>> Err(1).map(lambda i: i+1)
        2
        '''
        return fn(self.unwrap())

    def map_err(self, fn) -> Any:
        '''
        >>> Ok(1).map_err(lambda i: i+1)
        Ok<1>
        >>> Err(1).map_err(lambda i: i+1)
        Err<2>
        '''
        return Err(fn(self.unwrap())) if self.is_err() else self

    def and_then(self, fn) -> Any:
        '''
        >>> Ok(1).and_then(lambda i: i+1)
        Ok<2>
        >>> Err(1).and_then(lambda i: i+1)
        Err<1>
        '''
        return Ok(fn(self.unwrap())) if self.is_ok() else self

class Err(Ok, Exception):
    pass

Result = TypeVar('Result', Ok, Err)
