from .result import Ok, Err

status_code = {
    200: '200 OK'
}

class Request(object):
    def __init__(self, env):
        self.env = env
        self.method = env['REQUEST_METHOD'].upper()
        self.path = env['PATH_INFO'].lower()
        self.uri = env['RAW_URI']
        self.body = env['wsgi.input']
        self.next = (
            lambda path: ["{}/".format(x) for x in path[:-1]]+path[-1:]
        )(self.path.split('/'))

class Response(object):
    def __init__(self, start_res):
        self.start_res = start_res
        self.headers = {}
        self.body = b""
        self.status = 200

    def format(self):
#       TODO
        return [('Content-Type', 'text/html')]

    def ok(self, T=None):
        self.start_res(
            status_code[self.status],
            self.format()
        )
        return Ok(T or self.body)

    def err(self, E):
        return Err(E)
