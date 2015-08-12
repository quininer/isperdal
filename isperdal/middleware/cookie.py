from asyncio import coroutine
from http.cookies import SimpleCookie
from types import MethodType


def cookie(this, req, res):
    """
    TODO

    >>> from isperdal.request import Request
    >>> from isperdal import Microwave as u
    >>> env = {}
    >>> env['HTTP_COOKIE'] = ""
    >>> u("/").all()(cookie)
    '/'
    """
    @coroutine
    def method_cookies(self):
        if not hasattr(self, '__cookies'):
            self.__cookies = SimpleCookie((yield from self.header('Cookie')))
        return self.__cookies

    @coroutine
    def method_cookie(self, key):
        return (lambda v: v if v is None else v.value)((
            yield from self.cookies()
        ).get(key))

    req.cookies = MethodType(method_cookies, req)
    req.cookie = MethodType(method_cookie, req)
