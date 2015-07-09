from cgi import parse_qs, parse_multipart
from json import loads
from io import BytesIO

from .utils import Ok, Err


status_code = {
    200: '200 OK',
    302: '302 Found',
    400: '400 Bad Request'
}


class Request(object):
    def __init__(self, env):
        """
        >>> from io import BytesIO
        >>> req = Request({
        ...     "REQUEST_METHOD": "GET",
        ...     "QUERY_STRING": "bar=baz&foo[bar]=baz",
        ...     "RAW_URI": "/?bar=baz&foo[bar]=baz",
        ...     "PATH_INFO": "/",
        ...     "HTTP_USER_AGENT": "Test",
        ...     "wsgi.input": BytesIO()
        ... })
        >>> req.query("bar")
        'baz'
        >>> req.parms("foo")
        >>> req.querys["foo[bar]"]
        ['baz']
        >>> req.header("user_agent")
        'Test'
        """
        self.env = env
        self.method = (
            env['REQUEST_METHOD'].upper() if 'REQUEST_METHOD' in env else None
        )
        self.path = env.get('PATH_INFO') or '/'
        self.next = (
            lambda path: ["{}/".format(x) for x in path[:-1]]+path[-1:]
        )(self.path.split('/'))

        self._rest = {}

        (
            self._uri, self._body, self._query, self._post
        ) = [None, ]*4

    @property
    def uri(self):
        if self._uri is None:
            self._uri = self.env.get('RAW_URI')
        return self._uri

    @property
    def body(self):
        if self._body is None:
            body = self.env.get('wsgi.input')
            self._body = body or BytesIO()
        self._body.seek(0)
        return self._body

    def rest(self, name):
        return self.rest.get(name)

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
        return self.env.get("HTTP_{}".format(name.replace('-', '_').upper()))

    def post(self, name):
        if self._post is None:
            self._post = {
                'json': (lambda body: loads(body.read().decode())),
                # XXX 返回格式应该一致
                # 'plain': (lambda body: body.read().decode()),
                'form-data': (lambda body: {
                    x: y and y[-1] or ''
                    for x, y in parse_multipart(
                        body.decode(),
                        keep_blank_values=True
                    ).items()
                }),  # XXX or cgi.FieldStorage
                'x-www-form-urlencoded': (lambda body: {
                    x: y and y[-1] or ''
                    for x, y in parse_qs(
                        body.read().decode(),
                        keep_blank_values=True
                    ).items()
                }),
                'octet-stream': (lambda body: body),
                None: (lambda body: None)
            }[(
                lambda c:
                    c and
                    c.split(';')[0].split('/')[-1].lower() or
                    'x-www-form-urlencoded'
            )(self.header('Content-Type'))](self.body)
        return self._post.get(name)

    def parms(self, name):
        return (
            self.rest.get(name) or
            (lambda q: q and q[-1])(self.query(name)) or
            self.post(name) or
            None
        )


class Response(object):
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
            status_code[self.status_code],
            list(self.headers.items())
        )
        return Ok(self.body if T is None else T)

    def err(self, E):
        return Err(E)

    def redirect(self, url):
        if not (300 <= self.status_code < 400):
            self.status(302)
        return Err(url)
