class Result(object):
    """
    Result,
        from Rust.
    """

    def __init__(self, target):
        """
        >>> Ok(1)
        Ok<1>
        >>> Err('str')
        Err<'str'>
        """
        self.target = target

    def __repr__(self) -> str:
        return "{}<{!r}>".format(type(self).__name__, self.target)

    def unwrap(self):
        """
        >>> Ok(1).unwrap()
        1
        >>> Err(1).unwrap()
        1
        """
        return self.target

    def is_ok(self):
        """
        >>> Ok(1).is_ok()
        True
        >>> Err(1).is_ok()
        False
        """
        return type(self) == Ok

    def is_err(self):
        """
        >>> Err(1).is_err()
        True
        >>> Ok(1).is_err()
        False
        """
        return type(self) == Err

    def ok(self):
        """
        >>> Ok(1).ok()
        1
        >>> Err(1).ok()
        """
        return self.unwrap() if self.is_ok() else None

    def err(self):
        """
        >>> Err(1).err()
        1
        >>> Ok(1).err()
        """
        return self.unwrap() if self.is_err() else None

    def map(self, fn):
        """
        >>> Ok(1).map(lambda i: i+1)
        2
        >>> Err(1).map(lambda i: i+1)
        2
        """
        return fn(self.unwrap())

    def map_err(self, fn):
        """
        >>> Ok(1).map_err(lambda i: Err(i+1))
        Ok<1>
        >>> Err(1).map_err(lambda i: Err(i+1))
        Err<2>
        """
        return fn(self.unwrap()) if self.is_err() else self

    def and_then(self, fn):
        """
        >>> Ok(1).and_then(lambda i: Ok(i+1))
        Ok<2>
        >>> Err(1).and_then(lambda i: Ok(i+1))
        Err<1>
        """
        return fn(self.unwrap()) if self.is_ok() else self


class Ok(Result):
    pass


class Err(Result, Exception):
    """
    >>> try:
    ...     raise Err("err")
    ... except Err as e:
    ...     e
    Err<'err'>
    """
    pass


class lazy(object):
    """
    >>> class Bar:
    ...     id = 1
    ...     @lazy
    ...     def dict(self):
    ...         return {"a": self.id}
    >>> baz = Bar()
    >>> "a" in baz.dict
    True
    >>> baz.dict
    {'a': 1}
    """
    def __init__(self, fn):
        self._cache = None
        self._fn = fn

    def __get__(self, obj, cls):
        if self._cache is None:
            self._cache = self._fn(obj)
        return self._cache


class lazydict(dict):
    """
    >>> class Bar:
    ...     id = 1
    ...     @lazydict
    ...     def dict(self, key):
    ...         return self.id
    >>> baz = Bar()
    >>> "test" in baz.dict
    False
    >>> baz.dict.get("test")
    >>> baz.dict["test"]
    1
    >>> baz.dict.get("test")
    1
    """
    def __init__(self, fn):
        self._fn = fn
        self._obj = None

    def __get__(self, obj, cls):
        self._obj = obj
        return self

    def __getitem__(self, key):
        if key not in self:
            self.update({key: self._fn(self._obj, key)})
        return self.get(key)
