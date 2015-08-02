from cgi import FieldStorage
from urllib.parse import parse_qs, unquote_plus
from io import BytesIO
from http.client import responses as resps
from asyncio import coroutine

from .utils import Ok, Err


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
        self.next = (
            lambda path: ["{}/".format(p) for p in path[:-1]]+path[-1:]
        )(self.path.split('/'))
        self.stream = self.env.get('wsgi.input')

        self._rest = {}

        (self._body, self._query, self._form) = [None, ]*3

    @property
    @coroutine
    def body(self):
        """
        Request body IO.
            &asyncio
            read request stream, and returns from 0.

        - <BytesIO>
        """
        if self._body is None:
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
    def query(self, name):
        """
        Request query param.
            &asyncio
            1. always returns the first argument.
            2. not support nested parsing.
        ...
        """
        if self._query is None:
            self._query = parse_qs(
                self.env.get('QUERY_STRING'),
                keep_blank_values=True
            )

        return (lambda f="", *_: f)(*self._query.get(name, [None]))

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
    def form(self, name):
        """
        Request form param.
            &asyncio
            1. always returns the first argument.
        ...
        """
        if self._form is None:
            safe_env = {'QUERY_STRING': ""}
            for key in ('REQUEST_METHOD', 'CONTENT_TYPE', 'CONTENT_LENGTH'):
                if key in self.env:
                    safe_env[key] = self.env[key]
            fs = FieldStorage(
                fp=(yield from self.body),
                environ=safe_env,
                keep_blank_values=True
            )
            self._form = fs

        return self._form.getfirst(name)

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


class Response(object):
    """
    Response class.
    """

    def __init__(self, start_res):
        """
        init Response.

        + start_res<fn>     WSGI start_response
        """
        self.start_res = start_res
        self.headers = {}
        self.body = []
        self.status_code = 200
        self.status_text = None

    def status(self, code, text=None):
        """
        Set status.

        + code<int>         status code.
        + text<str>         status text.

        - self          Response object
        """
        self.status_code = code
        self.status_text = text
        return self

    def header(self, name, value):
        """
        Set header.

        + name<str>         header name.
        + value<str>        header value.

        ...
        """
        self.headers[name] = value
        return self

    def push(self, body):
        """
        Push content to body.

        + body<str>         body string.
            or bytes.

        ...
        """
        if isinstance(body, str):
            body = body.encode()

        bodysplit = (
            lambda b: [b[r:r+8192] for r in range(0, len(b), 8192)]
        )(body)

        self.body.extend(bodysplit)
        return self

    def ok(self, T=None):
        """
        Complete a response.
            return iterables object or `res.body`.

        + T                 iterables or coroutine

        - <Ok>
        """
        self.start_res(
            "{} {}".format(
                self.status_code,
                self.status_text or resps.get(self.status_code, "Unknown")
            ),
            self.headers.items()
        )
        return Ok(self.body if T is None else T)

    def err(self, E):
        """
        Throw a error.

        + E

        - <Err>
        """
        return Err(E)

    def redirect(self, url):
        if not (300 <= self.status_code < 400):
            self.status(302)
        return Err(url)
