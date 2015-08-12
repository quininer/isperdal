from asyncio import coroutine
from http.client import responses
from types import MethodType


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

    def __repr__(self):
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


@coroutine
def unok(fn):
    """
    >>> from asyncio import coroutine, get_event_loop
    >>> loop = get_event_loop()
    >>> loop.run_until_complete(unok(coroutine(
    ...     lambda: Ok(True)
    ... )()))
    True
    >>> loop.run_until_complete(unok(coroutine(
    ...     lambda: Ok(False)
    ... )()))
    False
    """
    return (yield from fn).ok()


def tobranch(path):
    """
    >>> tobranch("/one")
    ['/', 'one']
    >>> tobranch("/two/")
    ['/', 'two/', '']
    >>> tobranch("//")
    ['/', '/', '']
    """
    pathsplit = path.split('/')
    return ["{}/".format(p) for p in pathsplit[:-1]] + pathsplit[-1:]


def resp_status(status_code, status_text=None):
    """
    >>> resp_status(200)
    '200 OK'
    >>> resp_status(0, None)
    '200 OK'
    >>> resp_status(999)
    '999 Unknown'
    >>> resp_status(418, "I'm a teapot")
    "418 I'm a teapot"
    """
    return "{} {}".format(
        status_code or 200,
        status_text or responses.get(
            status_code or 200,
            "Unknown"
        )
    )

def mount(target, method, static=False):
    """
    >>> class Bar:
    ...     def __init__(self, num):
    ...         self.num = num
    >>> bar = Bar(1)

    >>> @mount(bar, 'add')
    ... def add(self, num):
    ...     self.num += num
    ...     return num
    >>> bar.add(2)
    2
    >>> @mount(Bar, 'echo', static=True)
    ... @property
    ... def echo(self):
    ...     return self.num
    >>> bar.echo
    3
    """
    def wrap_mount(fn):
        setattr(
            target, method,
            fn
            if static else
            MethodType(fn, target)
        )
    return wrap_mount
