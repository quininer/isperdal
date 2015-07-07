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
        return self.env.get('wsgi.input')

    @lazy
    def query(self):
        return parse_qs(self.env.get('QUERY_STRING'))

    @lazydict
    def header(self, name):
        return self.env.get("HTTP_{}".format(name.upper()))

    @lazy
    def post(self, name):
        # TODO 根据 content type 解析 json/query/form/text/bytes
        pass

    def parms(self, name):
        # FIXME 统一返回格式
        return (
            self.rest.get(name) or
            self.query.get(name) or
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
