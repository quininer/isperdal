from functools import reduce, partial
from .reqres import Request, Response
from .adapter import adapter
from .result import Ok, Err

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
            'HEAD': [],
            'GET': [],
            'POST': []
        }
        self.codes = {}

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
                    node.all(handle, methods)
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
            self.handles[method.upper()].append(handle)
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
        >>> app.append(Microwave('index/'), Microwave(':id'), methods=('GET',))(lambda: True)
        ':id'
        >>> app.subnode[-1]
        'index/'
        >>> app.subnode[0].subnode[-1]
        ':id'
        >>> app.subnode[0].subnode[0].handles['GET'][-1]()
        True
        """
        return partial(reduce((lambda x,y: x.then(y)), nodes).all, methods=methods)

    def head(self, *nodes):
        return self.route(*nodes, methods=('HEAD',))

    def get(self, *nodes):
        """
        Add GET method handles and node.

        >>> app = Microwave('/')
        >>> @app.get(Microwave('index'))
        ... def index(this, req, res):
        ...     return True
        >>> app.subnode[0].handles['GET'][0](None, None, None)
        True
        """
        return self.route(*nodes, methods=('GET',))

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
                self.codes[code] = handle
            return self
        return add_err

    def __handler(self, req, res):
        try:
            for handle in self.handles[req.method]:
                result = handle(self, req, res)
                if type(result) == Ok:
                    return result.ok()
                elif type(result) == Err:
                    raise result
        except Err as err:
            return self.codes[err.err()](req, res)

        if req.next:
            nextnode = req.next.poo(0)
            for node in filter((lambda n: n == nextnode), self.subnode):
                result = node.__handler(req, res)
                if result:
                    return result

        return res.body

    def run(self, host="127.0.0.1", port=8000, debug=True, server='aiohttp'):
        def application(env, start_res):
            req, res = Request(env), Response(start_res)
            return [self.__handler(req, res) if req.next.pop(0) == self else self.codes[404](req, res, None),]

        adapter[server](host, port, debug).run(application)
