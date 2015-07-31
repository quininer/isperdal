from cgi import FieldStorage
from urllib.parse import parse_qs, unquote_plus
from io import BytesIO
from http.client import responses as resps
import asyncio

from .utils import Ok, Err


class Request(object):
    """
    Request class.
    """

    def __init__(self, env):
        self.env = env
        self.method = (env.get('REQUEST_METHOD', 'GET')).upper()
        self.uri = env.get('RAW_URI')
        self.path = env.get('PATH_INFO', '/')
        self.next = (
            lambda path: ["{}/".format(p) for p in path[:-1]]+path[-1:]
        )(self.path.split('/'))
        self.stream = self.env.get('wsgi.input')
        self._body_cache = BytesIO()

        self._rest = {}

        (self._query, self._form) = [None, ]*2

    @property
    @asyncio.coroutine
    def body(self):
        self._body_cache.seek(0, 2)
        self._body_cache.write((yield from self.stream.read()) or b'')
        self._body_cache.seek(0)
        return self._body_cache

    @asyncio.coroutine
    def rest(self, name):
        return unquote_plus(self._rest.get(name, '')) or None

    @asyncio.coroutine
    def query(self, name):
        if self._query is None:
            self._query = {
                x: y and y[0] or ''
                for x, y in parse_qs(
                    self.env.get('QUERY_STRING'),
                    keep_blank_values=True
                ).items()
            }
        return self._query.get(name)

    @asyncio.coroutine
    def header(self, name):
        name = name.replace('-', '_').upper()
        return (
            self.env.get("HTTP_{}".format(name)) or
            self.env.get(name)
        )

    @asyncio.coroutine
    def form(self, name):
        if self._form is None:
            safe_env = {'QUERY_STRING': ''}
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

    @asyncio.coroutine
    def parms(self, name):
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
        self.start_res = start_res
        self.headers = {}
        self.body = []
        self.status_code = 200
        self.status_text = None

    def status(self, code, text=None):
        self.status_code = code
        self.status_text = text
        return self

    def header(self, name, value):
        self.headers[name] = value
        return self

    def push(self, body):
        self.body.append(body.encode() if isinstance(body, str) else body)
        return self

    def ok(self, T=None):
        self.start_res(
            "{} {}".format(
                self.status_code,
                self.status_text or resps.get(self.status_code, "Unknown")
            ),
            list(self.headers.items())
        )
        return Ok(self.body if T is None else T)

    def err(self, E):
        return Err(E)

    def redirect(self, url):
        if not (300 <= self.status_code < 400):
            self.status(302)
        return Err(url)
