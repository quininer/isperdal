from asyncio import coroutine
from http.cookies import SimpleCookie

from isperdal.utils import mount


def cookie(this, req, res):
    """
    >>> from isperdal.request import Request
    >>> from isperdal.response import Response
    >>> from isperdal import Microwave as u

    >>> from asyncio import coroutine, get_event_loop
    >>> loop = get_event_loop()

    >>> env = {}
    >>> env['HTTP_COOKIE'] = "bar=baz"
    >>> req, res = Request(env), Response(lambda *_: None)

    >>> cookie(None, req, res)

    >>> loop.run_until_complete(req.cookies())
    <SimpleCookie: bar='baz'>
    >>> loop.run_until_complete(req.cookie('bar'))
    'baz'

    >>> res.cookie('foo', 'bar').cookies
    <SimpleCookie: foo='bar'>
    >>> res.hook[-1](res)
    >>> res.headers['Set-Cookie']
    'foo=bar'
    """
    @mount(req, 'cookies')
    @coroutine
    def req_cookies(self):
        if not hasattr(self, '__cookies'):
            self.__cookies = SimpleCookie((yield from self.header('Cookie')))
        return self.__cookies

    @mount(req, 'cookie')
    @coroutine
    def req_cookie(self, key):
        return (lambda v: v if v is None else v.value)((
            yield from self.cookies()
        ).get(key))

    res.cookies = SimpleCookie()

    @mount(res, 'cookie')
    def res_cookie(self, key, value):
        if isinstance(value, dict):
            if key in res.__cookie:
                self.cookies[key] = value.get('value', "")
            for k, v in value.items():
                if k in (
                    'expires',
                    'max-age',
                    'comment',
                    'version',
                    'domain',
                    'path',
                    'httponly',
                    'secure'
                ):
                    res.cookies[key][k] = v
        else:
            res.cookies[key] = value

        return self

    @res.hook.append
    def hook_cookie(res):
        if hasattr(res, 'cookies') and res.cookies:
            res.header(*res.cookies.output().split(': ', 1))
