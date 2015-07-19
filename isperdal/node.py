from functools import reduce
from .reqres import Request, Response
from .adapter import adapter
from .utils import Result, Ok, Err


class Microwave(str):
    """
    Microwave Node.
    > 奥塔究竟怎么设计我的喉咙的？

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
            400: (
                lambda this, req, res, err:
                    res.push("400, {}".format(err))
            ),
            404: (
                lambda this, req, res, err:
                    res.push("404, {}".format(err))
            ),
        }

    def route(self, *nodes, methods=('HEAD', 'GET', 'POST')):
        """
        The basic route map.
        """
        def add_route(*handles):
            for node in nodes:
                self.add(node)
                for handle in handles:
                    node.all(handle, methods)
            return self
        return add_route

    def all(self, handle, methods=None):
        """
        Add handle method for the node.
        """
        for method in methods or self.handles.keys():
            self.handles[method.upper()].append(handle)
        return self

    def add(self, node):
        """
        Add a subnode.
        """
        self.subnode.append(node)
        return self

    def then(self, node):
        """
        Add a subnode, then..
        """
        self.add(node)
        return node

    def append(*nodes, methods=('HEAD', 'GET', 'POST')):
        """
        Add mutlt subnode, then..
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

    def socket(self, *nodes):
        pass

    def get(self, *nodes):
        """
        Add GET method handles to node.
        """
        return self.route(*nodes, methods=('GET',))

    def head(self, *nodes):
        return self.route(*nodes, methods=('HEAD',))

    def post(self, *nodes):
        return self.route(*nodes, methods=('POST',))

    def err(self, *codes):
        """
        Add Error handles.
        """
        def add_err(handle):
            for code in codes:
                self.codes[code] = handle
            return self
        return add_err

    def __handler(self, req, res):
        """
        Request handle.
        """
        try:
            if req.method not in self.handles:
                raise res.status(400).err("Method can't understand.")
            for handle in self.handles[req.method]:
                result = handle(self, req, res)
                if isinstance(result, Result):
                    if result.is_ok():
                        return result
                    else:
                        raise result

            if req.next:
                nextnode = req.next.pop(0)
                for node in self.subnode:
                    if len(node) >= 3 and node[:2] == ":!":
                        req._rest[
                            node[2:].rstrip('/')
                        ] = "".join([nextnode]+req.next)
                    elif len(node) >= 2 and node[0] == ":":
                        req._rest[
                            node[1:].rstrip('/')
                        ] = nextnode.rstrip('/')
                    elif nextnode != node:
                        continue
                    result = node.__handler(req, res)
                    if isinstance(result, Ok):
                        return result
            if not res.body:
                raise res.status(404).err("Not Found")

        except Err as err:
            if res.status_code in self.codes:
                result = self.codes[res.status_code](self, req, res, err.err())
                if isinstance(result, Ok):
                    return result
            else:
                raise err

        return res.ok()

    def __call__(self, env, start_res):
        req, res = Request(env), Response(start_res)
        return (
            self.__handler(req, res)
            if req.next.pop(0) == self else
            self.codes[400](req, res, "URI Error.")
        ).ok()

    def run(
        self, host="127.0.0.1", port=8000,
        debug=True, ssl=False, server='aiohttp'
    ):
        adapter[server](host, port, debug, ssl).run(self)
