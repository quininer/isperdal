from asyncio import async, coroutine
from functools import reduce

from .reqres import Request, Response
from .adapter import adapter
from .utils import Result, Err


class Microwave(str):
    """
    Microwave Node.
    > 奥塔究竟怎么设计我的喉咙的？

    >>> Microwave("/")
    '/'
    """

    def __init__(self, *args, **kwargs):
        self.subnode = []
        self.handles = {
            'OPTION': [],
            'GET': [],
            'HEAD': [],
            'POST': [],
            'PUT': [],
            'DELETE': [],
            'TRACE': [],
            'CONNECT': [],
            'PATCH': []
        }
        self.codes = {
            '400': (
                lambda this, req, res, err:
                    res.push("400, {}".format(err))
            ),
        }

    def route(self, *nodes, methods=('HEAD', 'GET', 'POST')):
        """
        The basic route map.

        >>> app = Microwave('/')
        >>> @app.route(Microwave('index'))
        ... def index(this, req, res):
        ...     return True
        >>> index
        '/'
        >>> app.subnode[-1]
        'index'
        >>> app.subnode[0].handles['GET'][-1](None, None, None)
        True
        """
        def add_route(*handles):
            for node in nodes:
                self.add(node)
                for handle in handles:
                    node.all(coroutine(handle), methods)
            return self
        return add_route

    def all(self, handle, methods=None):
        """
        Add handle method for the node.

        >>> app = Microwave('/')
        >>> @app.all
        ... def all(this, req, res):
        ...     return True
        >>> all
        '/'
        >>> app.handles['GET'] == app.handles['POST'] == app.handles['HEAD']
        True
        >>> app.handles['GET'][0](None, None, None)
        True
        >>> app.all((lambda: False), methods=['HEAD']).handles['HEAD'][-1]()
        False
        """
        for method in methods or self.handles.keys():
            self.handles[method.upper()].append(coroutine(handle))
        return self

    def add(self, node):
        """
        Add a subnode.

        >>> app = Microwave('/')
        >>> app.add(Microwave('index'))
        '/'
        >>> app.subnode[0]
        'index'
        >>> len(app.subnode)
        1
        """
        self.subnode.append(node)
        return self

    def then(self, node):
        """
        Add a subnode, then..

        >>> app = Microwave('/')
        >>> app.then(Microwave('index'))
        'index'
        >>> app.then(Microwave('posts/')).then(Microwave(':id'))
        ':id'
        """
        self.add(node)
        return node

    def append(*nodes, methods=('HEAD', 'GET', 'POST')):
        """
        Add mutlt subnode, then..

        >>> app = Microwave('/')
        >>> app.append(
        ...     Microwave('index/'), Microwave(':id'), methods=('GET',)
        ... )(lambda: True)
        '/'
        >>> app.subnode[-1]
        'index/'
        >>> app.subnode[0].subnode[-1]
        ':id'
        >>> app.subnode[0].subnode[0].handles['GET'][-1]()
        True
        """
        self = nodes[0]

        def append_wrap(nodeall, methods):
            def all_wrap(fn):
                nodeall(fn, methods=methods)
                return self
            return all_wrap

        return append_wrap(
            reduce((lambda x, y: x.then(y)), nodes).all,
            methods
        )

    def get(self, *nodes):
        """
        Add GET method handles to node.

        >>> app = Microwave('/')
        >>> @app.get(Microwave('index'))
        ... def index(this, req, res):
        ...     return True
        >>> app.subnode[0].handles['GET'][0](None, None, None)
        True
        """
        return self.route(*nodes, methods=('GET',))

    def head(self, *nodes):
        return self.route(*nodes, methods=('HEAD',))

    def post(self, *nodes):
        return self.route(*nodes, methods=('POST',))

    def err(self, *codes):
        """
        Add Error handles.

        >>> app = Microwave('/')
        >>> @app.err(404)
        ... def err404(this, req, res, err):
        ...     return True
        >>> app.codes[404](None, None, None, None)
        True
        """
        def add_err(handle):
            for code in codes:
                self.codes[code] = coroutine(handle)
            return self
        return add_err

    @coroutine
    def trigger(self, req, res, code, message):
        result = yield from self.codes[code](req, res, message)
        return result.ok()

    @coroutine
    def __handler(self, req, res):
        """
        Request handle.

        >>> class test: pass
        >>> req, res = test(), test()
        >>> req.rest = {}
        >>> req.next = []
        >>> req.method = 'GET'
        >>> res.status = (lambda code: res)
        >>> res.push = (lambda body: Ok(body))
        >>> res.ok = (lambda body: Ok(body))
        >>> res.err = (lambda err: Err(err))

        >>> Microwave('/').all(
        ...     lambda this, req, res: res.push(b"test")
        ... )._Microwave__handler(req, res)
        Ok<b'test'>
        >>> req.next = ['post/', '1']
        >>> Microwave('/').append(
        ...     Microwave('post/'), Microwave(':id')
        ... )(
        ...     lambda this, req, res: res.push(req.rest['id'])
        ... )._Microwave__handler(req, res)
        Ok<'1'>
        >>> res.status_code = 404
        >>> Microwave('/').err(404)(
        ...     lambda this, req, res, err: res.ok(err)
        ... ).all(
        ...     lambda this, req, res: res.status(404).err(b"test")
        ... )._Microwave__handler(req, res)
        Ok<b'test'>
        >>> req.next = ['assets/', 'file/', 'test.png']
        >>> Microwave('/').append(
        ...     Microwave('assets/'), Microwave(':!path')
        ... )(
        ...     lambda this, req, res: res.push(req.rest['path'])
        ... )._Microwave__handler(req, res)
        Ok<'file/test.png'>
        """
        try:
            if req.method not in self.handles:
                raise res.status(400).err("Method can't understand.")
            for handle in self.handles[req.method]:
                result = yield from handle(self, req, res)
                if isinstance(result, Result):
                    if result.is_ok():
                        return result.ok()
                    else:
                        raise result

            if req.next:
                nextnode = req.next.pop(0)
                for node in self.subnode:
                    if len(node) >= 3 and node[:2] == ":!":
                        req._rest[
                            node[2:].rstrip('/')
                        ] = ["".join([nextnode]+req.next), ]
                    elif len(node) >= 2 and node[0] == ":":
                        req._rest[
                            node[1:].rstrip('/')
                        ] = [nextnode.rstrip('/'), ]
                    elif nextnode != node:
                        continue
                    result = yield from node.__handler(req, res)
                    if result:
                        return result

        except Err as err:
            if res.status_code in self.codes:
                result = yield from self.trigger(req, res, res.status_code, err.err())
                return result
            else:
                raise err

        return res.ok().ok()

    def __call__(self, env, start_res):
        req, res = Request(env), Response(start_res)
        return async(
            self.__handler(req, res)
            if req.next.pop(0) == self else
            self.trigger(req, res, 400, "URL Error.")
        )

    def run(self, host="127.0.0.1", port=8000, debug=True, ssl=False, server='aiohttp'):
        adapter[server](host, port, debug, ssl).run(self)
