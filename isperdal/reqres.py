from cgi import parse_qs

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
        self.path = (
            env['PATH_INFO']
            if 'PATH_INFO' in env and env['PATH_INFO'] else
            '/'
        )
        self.next = (
            lambda path: ["{}/".format(x) for x in path[:-1]]+path[-1:]
        )(self.path.split('/'))

        self.rest = {}

    @lazy
    def uri(self):
        return self.env['RAW_URI'] if 'RAW_URI' in self.env else None

    @lazy
    def body(self):
        return self.env['wsgi.input'] if 'wsgi.input' in self.env else None

    @lazy
    def query(self):
        return parse_qs(self.env['QUERY_STRING']) if 'QUERY_STRING' in self.env else {}

    @lazydict
    def header(self, name):
        name = "HTTP_{}".format(name.upper())
        return self.env[name] if name in self.env else None

    @lazy
    def post(self, name, num=0):
        # TODO 根据 content type 解析 json/query/form/text/bytes
        pass

    def parms(self, name, num=0):
        # FIXME 这什么乱七八糟的...
        if name in self.rest:
            return self.rest[name]
        value = self.query(name, num)
        if value:
            return value
        value = self.post(name, num)
        if value:
            return value
        return None


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
