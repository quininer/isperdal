from cgi import parse_qs, parse_multipart
from json import loads
from io import BytesIO

from .utils import Ok, Err, lazydict, lazy


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

        self.rest = {}

    @lazy
    def uri(self):
        return self.env.get('RAW_URI')

    @lazy
    def body(self):
        return self.env.get('wsgi.input') or BytesIO()

    @lazy
    def query(self):
        return parse_qs(self.env.get('QUERY_STRING'), keep_blank_values=True)

    @lazydict
    def header(self, name):
        return self.env.get("HTTP_{}".format(name.replace('-', '_').upper()))

    @lazy
    def post(self):
        self.body.seek(0)

        return {
            'json': (lambda body: loads(body.read().decode())),
            'plain': (lambda body: body.read().decode()),
            # XXX 统一输出格式
            'form-data': (lambda body: parse_multipart(body.decode())), # XXX or cgi.FieldStorage
            'x-www-form-urlencoded': (lambda body: parse_qs(body.read().decode(), keep_blank_values=True)),
            'octet-stream': (lambda body: body),
            None: (lambda body: None)
        }[(
            lambda c: c and c.split(';')[0].split('/')[-1].lower() or 'x-www-form-urlencoded'
        )(self.header['Content-Type'])](self.body)

    def parms(self, name):
        return (
            self.rest.get(name) or
            (lambda q: q and q[-1])(self.query.get(name)) or
            self.post[name] or
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
