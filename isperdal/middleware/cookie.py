from asyncio import coroutine
from http.cookies import SimpleCookie

from isperdal.utils import mount


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
    def hook_cookie(self):
        if hasattr(self, 'cookies') and self.cookies:
            self.header(*self.cookies.output().split(': ', 1))
