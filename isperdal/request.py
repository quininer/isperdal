from cgi import FieldStorage
from urllib.parse import parse_qs, unquote_plus
from io import BytesIO
from asyncio import coroutine

from .utils import tobranch


class Request(object):
    """
    Request class.
    """

    def __init__(self, env):
        """
        init Request.

        + env<dict>     WSGI env.
        """
        self.env = env
        self.method = env.get('REQUEST_METHOD', "GET").upper()
        self.uri = env.get('RAW_URI')
        self.path = env.get('PATH_INFO', "/")
        self.branches = tobranch(self.path)
        self.stream = self.env.get('wsgi.input')

        self._rest = {}

    @coroutine
    def body(self):
        """
        Request body IO.
            &asyncio
            read request stream, and returns from 0.

        - <BytesIO>
        """
        if not hasattr(self, '_body'):
            self._body = BytesIO()

        self._body.seek(0, 2)
        self._body.write((yield from self.stream.read()) or b"")
        self._body.seek(0)

        return self._body

    @coroutine
    def rest(self, name):
        """
        Request REST style param.
            &asyncio
            1. param values allowed to be overwritten.

        + name<str>     param name

        - <str>         param value
        - <None>
        """
        return unquote_plus(self._rest.get(name, '')) or None

    @coroutine
    def querys(self):
        if not hasattr(self, '__querys'):
            self.__querys = parse_qs(
                self.env.get('QUERY_STRING'),
                keep_blank_values=True
            )
        return self.__querys

    @coroutine
    def query(self, name):
        """
        Request query param.
            &asyncio
            1. always returns the first argument.
            2. not support nested parsing.
        ...
        """
        return (lambda f="", *_: f)(*(
            yield from self.querys()
        ).get(name, [None]))

    @coroutine
    def header(self, name):
        """
        Request header param.
            &asyncio
            1. Priority resolve HTTP_NAME format head.
                eg: HTTP_USER_AGENT
                eg: REMOTE_ADDR
            2. Automatic conversion case.
        ...
        """
        name = name.replace('-', '_').upper()
        return (
            self.env.get("HTTP_{}".format(name)) or
            self.env.get(name)
        )

    @coroutine
    def forms(self):
        if not hasattr(self, '__forms'):
            safe_env = {'QUERY_STRING': ""}
            for key in ('REQUEST_METHOD', 'CONTENT_TYPE', 'CONTENT_LENGTH'):
                if key in self.env:
                    safe_env[key] = self.env[key]
            fs = FieldStorage(
                fp=(yield from self.body()),
                environ=safe_env,
                keep_blank_values=True
            )
            self.__forms = fs
        return self.__forms

    @coroutine
    def form(self, name):
        """
        Request form param.
            &asyncio
            1. always returns the first argument.
        ...
        """
        return (yield from self.forms()).getfirst(name)

    @coroutine
    def parms(self, name):
        """
        Request all param.
            &asyncio
        ...
        """
        return (
            (yield from self.rest(name)) or
            (yield from self.query(name)) or
            (yield from self.form(name)) or
            None
        )
