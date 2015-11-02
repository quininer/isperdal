from asyncio import iscoroutinefunction, coroutine

from .node import Microwave
from .websocket import WebSocket


def only(handle):
    """
    not next node. only it.

    + <function>(&)     handle function (asyncio)

    - <function>(&)     only wrap.

    >>> from isperdal.utils import aiotest
    >>> req = type('Request', (), {
    ...     'next': []
    ... })()
    >>> nreq = type('Request', (), {
    ...     'next': ['next']
    ... })()

    >>> @coroutine
    ... @only
    ... def bar(this, req, res):
    ...     return this

    >>> @only
    ... @coroutine
    ... def baz(this, req, res):
    ...     return this

    >>> @aiotest
    ... def test():
    ...     assert (yield from bar("one", req, None)) == "one"
    ...     assert (yield from bar("one", nreq, None)) == None
    ...     assert (yield from baz("one", req, None)) == "one"
    ...     assert (yield from baz("one", nreq, None)) == None
    ...     return True

    >>> test()
    True
    """
    isaio = iscoroutinefunction(handle)

    def only_wrap(this, req, res):
        if not req.next:
            return (
                (yield from handle(this, req, res))
                if isaio else
                handle(this, req, res)
            )

    return (
        coroutine(only_wrap)
        if isaio else
        only_wrap
    )
