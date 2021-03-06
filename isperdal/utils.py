from asyncio import coroutine, get_event_loop
from http.client import responses
from types import MethodType
from functools import wraps


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
        return self.target if self.is_ok() else None

    def err(self):
        """
        >>> Err(1).err()
        1
        >>> Ok(1).err()
        """
        return self.target if self.is_err() else None

    def map(self, fn):
        """
        >>> Ok(1).map(lambda i: i+1)
        Ok<2>
        >>> Err(1).map(lambda i: i+1)
        Err<1>
        """
        return Ok(fn(self.target)) if self.is_ok() else self

    def map_err(self, fn):
        """
        >>> Ok(1).map_err(lambda i: i+1)
        Ok<1>
        >>> Err(1).map_err(lambda i: i+1)
        Err<2>
        """
        return Err(fn(self.target)) if self.is_err() else self


class Ok(Result):
    """
    >>> bool(Ok(False))
    True
    """
    def __bool__(self):
        return True


class Err(Result, Exception):
    """
    >>> try:
    ...     raise Err("err")
    ... except Err as e:
    ...     e
    Err<'err'>
    >>> bool(Err(True))
    False
    """
    def __bool__(self):
        return False


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


def aiotest(fn):
    """
    >>> @aiotest
    ... def foo(bar):
    ...     assert bar == "BAR"
    >>> foo("BAR")

    >>> @coroutine
    ... def baz():
    ...     return "BAZ"
    >>> @aiotest
    ... def foo2(baz):
    ...     return (yield from baz())

    >>> foo2(baz)
    'BAZ'
    """
    @wraps(fn)
    def aio_wrap(*args, **kwargs):
        loop = get_event_loop()
        return loop.run_until_complete(coroutine(fn)(*args, **kwargs))
    return aio_wrap
