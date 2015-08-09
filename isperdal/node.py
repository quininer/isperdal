from asyncio import async, coroutine
from functools import reduce
from types import FunctionType

from .request import Request
from .response import Response
from .adapter import AioHTTPServer
from .utils import Result, Ok, Err, unok


class Microwave(str):
    """
    Microwave Node.
    > 奥塔究竟怎么设计我的喉咙的？

    """

    def __init__(self, *args, **kwargs):
        """
        init node.

        + node          str.
        """
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
        self.codes = {}
        self.codes[400] = self.codes[404] = coroutine(
            lambda this, req, res, err:
                res.push("{} {}".format(res.status_code, err))
        )

    def route(self, *nodes, methods=('HEAD', 'GET', 'POST')):
        """
        The basic route map.

        + *nodes<node>          multiple node object.
        + methods<tuple>        iterables, value is `self.handles` key.

        - <function>    wrap function
            + *handles      multiple handle function.
                | this          node object.
                | req           Request object.
                | res           Response object.

                @ Result object.

            - self          self node.
        """
        def add_route(*handles):
            for node in nodes:
                self.add(node)
                node.all(methods)(*map((
                    lambda h:
                        coroutine(h) if isinstance(h, FunctionType) else h
                ), handles))
            return self
        return add_route

    def all(self, methods=None):
        """
        Add handle method for the node.

        + methods<tuple>        iterables, value is `self.handles` key.

        - <function>            wrap function
            ...
        """
        def all_wrap(*handles):
            for method in (methods or self.handles.keys()):
                self.handles[method.upper()].extend(map((
                    lambda h:
                        coroutine(h) if isinstance(h, FunctionType) else h
                ), handles))
            return self
        return all_wrap

    def add(self, node):
        """
        Add a subnode.

        + node<node>            node object.

        - self                  self node.
        """
        self.subnode.append(node)
        return self

    def then(self, node):
        """
        Add a subnode, then..

        + node<node>            node object.

        - <node>                node.
        """
        self.add(node)
        return node

    def append(*nodes, methods=('HEAD', 'GET', 'POST')):
        """
        Add multiple subnode, then..

        + *nodes<node>          multiple node object.
        + methods<tuple>        iterables, value is `self.handles` key.

        - <function>    wrap function
            ...
        """
        self = nodes[0]

        def append_wrap(*handles):
            reduce((lambda x, y: x.then(y)), nodes).all(methods)(*handles)
            return self
        return append_wrap

    def get(self, *nodes):
        """
        Add GET method handles to node.

        + *nodes<node>          multiple node object.

        - <function>            wrap function
            ...
        """
        return self.route(*nodes, methods=('GET',))

    def head(self, *nodes):
        return self.route(*nodes, methods=('HEAD',))

    def post(self, *nodes):
        return self.route(*nodes, methods=('POST',))

    def err(self, *codes):
        """
        Add Error handles.

        + *codes<int>           multiple status code.

        - <function>    wrap function
            + handle        handle function.
                | this          node object.
                | req           Request object.
                | res           Response object.
                | err           Error message.

                @ Result object.

            - self          self node.
        """
        def add_err(handle):
            for code in codes:
                self.codes[code] = coroutine(handle)
            return self
        return add_err

    @coroutine
    def trigger(self, req, res, code, message):
        """
        Error trigger.
            &asyncio

        + req               Request object.
        + res               Response object.
        + code<int>         status code.
        + err<T>            Error message.

        - Result object.
        """
        res.status(code)
        result = yield from self.codes[code](self, req, res, message)
        return result if isinstance(result, Ok) else res.ok()

    @coroutine
    def __handler(self, req, res):
        """
        Request handle.
        """
        try:
            if req.method not in self.handles:
                raise res.status(400).err("Method can't understand.")
            for handle in self.handles[req.method]:
                if isinstance(handle, type):
                    # and issubclass(handle, WebSocket):
                    if not req.env.get('websocket'):
                        continue
                    result = yield from handle(self, req, res)()
                else:
                    result = yield from handle(self, req, res)

                if isinstance(result, Result):
                    if result.is_ok():
                        return result
                    else:
                        raise result

            if req.branches:
                nextnode = req.branches.pop(0)
                for node in self.subnode:
                    if len(node) >= 3 and node[:2] == ":!":
                        req._rest[
                            node[2:].rstrip('/')
                        ] = "".join([nextnode]+req.branches)
                    elif len(node) >= 2 and node[0] == ":":
                        req._rest[
                            node[1:].rstrip('/')
                        ] = nextnode.rstrip('/')
                    elif nextnode != node:
                        continue
                    result = yield from node.__handler(req, res)
                    if isinstance(result, Ok):
                        return result

            if not res.body:
                raise res.status(404).err("Not Found")

        except Err as err:
            if res.status_code in self.codes:
                result = yield from self.trigger(
                    req, res, res.status_code, err.err()
                )
                if isinstance(result, Ok):
                    return result
            else:
                raise err

        return res.ok()

    def __call__(self, env, start_response):
        req, res = Request(env), Response(start_response)
        return async(unok(
            self.__handler(req, res)
            if req.branches.pop(0) == self else
            self.trigger(
                req, res, 400, "URL Error"
            )
        ))

    def run(self, host="127.0.0.1", port=8000, debug=True, ssl=False):
        AioHTTPServer(host, port, debug, ssl).run(self)
