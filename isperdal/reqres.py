from cgi import FieldStorage
from urllib.parse import parse_qs
from io import BytesIO
from http.client import responses as res_status

from .utils import Ok, Err


class Request(object):
    """
    Request class.
    """

    def __init__(self, env):
        self.env = env
        self.method = (env.get('REQUEST_METHOD') or 'GET').upper()
        self.uri = env.get('RAW_URI')
        self.path = env.get('PATH_INFO') or '/'
        self.next = (
            lambda path: ["{}/".format(x) for x in path[:-1]]+path[-1:]
        )(self.path.split('/'))

        self._rest = {}

        (self._body, self._query, self._form) = [None, ]*3

    @property
    def body(self):
        if self._body is None:
            self._body = self.env.get('wsgi.input') or BytesIO()
        self._body.seek(0)
        return self._body

    def rest(self, name):
        return self._rest.get(name)

    def query(self, name):
        if self._query is None:
            self._query = {
                x: y and y[-1] or ''
                for x, y in parse_qs(
                    self.env.get('QUERY_STRING'),
                    keep_blank_values=True
                ).items()
            }
        return self._query.get(name)

    def header(self, name):
        name = name.replace('-', '_').upper()
        return (
            self.env.get("HTTP_{}".format(name)) or
            self.env.get(name)
        )

    def form(self, name):
        if self._form is None:
            safe_env = {'QUERY_STRING': ''}
            for key in ('REQUEST_METHOD', 'CONTENT_TYPE', 'CONTENT_LENGTH'):
                if key in self.env:
                    safe_env[key] = self.env[key]
            fs = FieldStorage(
                fp=self.body,
                environ=safe_env,
                keep_blank_values=True
            )
            self._form = fs
        return self._form.getfirst(name)

    def parms(self, name):
        return (
            self.rest(name) or
            self.query(name) or
            self.form(name) or
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

    def status(self, code=None):
        if code is None:
            return self.status
        self.status = code
        return self

    def header(self, name, value):
        self.headers[name] = value
        return self

    def push(self, body):
        self.body.append((
            lambda body: body.encode() if isinstance(body, str) else body
        )(body))
        return self

    def ok(self, T=None):
        self.start_res(
            (
                lambda code:
                    "{} {}".format(code, res_status.get(code) or 'Unknown')
            )(self.status_code),
            list(self.headers.items())
        )
        return Ok(self.body if T is None else T)

    def err(self, E):
        return Err(E)

    def redirect(self, url):
        if not (300 <= self.status_code < 400):
            self.status(302)
        return Err(url)
