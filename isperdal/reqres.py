from cgi import parse_qs

from .result import Ok, Err


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
        self.uri = env['RAW_URI'] if 'RAW_URI' in env else None
        self.body = env['wsgi.input'] if 'wsgi.input' in env else None
        self.next = (
            lambda path: ["{}/".format(x) for x in path[:-1]]+path[-1:]
        )(self.path.split('/'))

        self.rest = {}
        self.querys = (
            parse_qs(env['QUERY_STRING']) if 'QUERY_STRING' in env else None
        )

    def query(self, name, num=0):
        """
        query method.
        """
        value = self.querys[name] if name in self.querys else None
        return value[num] if value else None

    def header(self, name):
        # FIXME 给我用带缓存的懒解析！
        name = "HTTP_{}".format(name.upper())
        return self.env[name] if name in self.env else None

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

    def redirect(self, url, *, code=302):
        # FIXME 用 res.status 设置code
        self.status(code)
        return Err(url)
