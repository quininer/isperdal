from copy import copy
from asyncio import async, coroutine, iscoroutinefunction
from functools import reduce
from types import FunctionType
from traceback import format_exc

from .request import Request
from .response import Response
from .adapter import AioHTTPServer
from .utils import Result, Ok, Err, unok


codes = {
    302: coroutine(
        lambda this, req, res, err:
            res.header("Location", err).ok()
    ),
    400: coroutine(
        lambda this, req, res, err:
            res.push("400 {}".format(err)).ok()
    ),
    404: coroutine(
        lambda this, req, res, err:
            res.push("404 {}".format(err)).ok()
    ),
    500: coroutine(
        lambda this, req, res, err:
            print(err) or res.push(
                err if this.debug else "500 Unknown Error"
            ).ok()
    )
}


class Node(str):
    """
    Microwave Node.
    """

    debug = True

    def __init__(self, *args, **kwargs):
        """
        init node.

        + node          str.
        """
        self.subnode = []
        self.handles = {
            m: [] for m in (
                'OPTION',
                'GET',
                'HEAD',
                'POST',
                'PUT',
                'DELETE',
                'TRACE',
                'CONNECT',
                'PATCH'
            )
        }
        self.codes = {}

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
                self.then(node).all(methods)(*handles)
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
                    lambda handle:
                        coroutine(handle)
                        if (
                            isinstance(handle, FunctionType) and
                            not iscoroutinefunction(handle)
                        ) else
                        handle
                ), handles))
            return self
        return all_wrap

    def add(self, node):
        """
        Add a subnode.

        + node<node>            node object.

        - self                  self node.
        """
        if node in self.subnode:
            exist = self.subnode[self.subnode.index(node)]
            for m in node.handles:
                exist.handles[m].extend(node.handles[m])

            for n in node.subnode:
                exist.add(n)
        else:
            self.subnode.append(node)

        return self

    def then(self, node):
        """
        Add a subnode, then..

        + node<node>            node object.

        - <node>                node.
        """
        self.add(node)
        return self.subnode[self.subnode.index(node)]

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
                self.codes[code] = (
                    handle
                    if iscoroutinefunction(handle) else
                    coroutine(handle)
                )
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
        result = yield from (
            self.codes if code in self.codes else codes
        )[code](self, req, res, message)
        return result

    @coroutine
    def handler(self, req, res, branches):
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
                    # NOTE: why? Python 3.4- always returns None???

                if isinstance(result, Result):
                    if result.is_ok():
                        return result
                    else:
                        raise result

            if branches:
                nextnode = branches.pop(0)
                for node in self.subnode:
                    if node.startswith(":!"):
                        req._rest[node[2:]] = "".join(
                            [nextnode] + branches
                        )
                    elif node.startswith(":"):
                        if node.endswith("/") != nextnode.endswith("/"):
                            continue
                        req._rest[node[1:].rstrip("/")] = nextnode.rstrip("/")
                    elif nextnode != node:
                        continue
                    result = yield from node.handler(req, res, copy(branches))
                    if isinstance(result, Ok):
                        return result

            if not res.done:
                raise res.status(404).err("Not Found")
            else:
                return res.ok()

        except Err as err:
            if res.status_code in self.codes:
                result = yield from self.trigger(
                    req, res, res.status_code, err.err()
                )
                if isinstance(result, Ok):
                    return result

            raise err

    @coroutine
    def start(self, req, res):
        try:
            result = yield from self.handler(req, res, copy(req.branches))
        except Exception as err:
            if isinstance(err, Err) and res.status_code in codes:
                result = yield from self.trigger(
                    req, res, res.status_code, err.err()
                )
            else:
                result = yield from self.trigger(req, res, 500, format_exc())

        return result

    def __call__(self, env, start_response):
        req, res = Request(env), Response(start_response)
        return async(unok(
            self.start(req, res)
            if req.branches.pop(0) == self else
            self.trigger(req, res, 400, "URL Error")
        ))

    def run(self, host="127.0.0.1", port=8000, debug=True, ssl=()):
        Node.debug = debug
        AioHTTPServer(host, port, debug, ssl).run(self.__call__)
