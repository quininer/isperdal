# from .reqres import Request, Response

class Microwave(str):
    """
    Microwave.
    """

    subnode = set()
    handles = {
        'HEAD': [],
        'GET': [],
        'POST': []
    }
    codes = {}

    def route(self, *nodes, methods=('HEAD', 'GET', 'POST')):
        def add_route(*handles):
            for node in nodes:
                self.add(node)
                for handle in handles:
                    node.all(handle, methods)
            return self
        return add_route

    def all(self, handle, methods=None):
        for method in methods or self.handles.keys():
            self.handles[method].append(handle)
        return self

    def add(self, node):
        if node in self.subnode:
            pass

    def then(self, node):
        self.add(node)
        return node

    def head(self, *nodes):
        return self.route(*nodes)

    def get(self, *nodes):
        return self.route(*nodes)

    def post(self, *nodes):
        return self.route(*nodes)

    def err(self, *codes):
        def add_err(handle):
            for code in codes:
                self.codes[code] = handle
            return self
        return add_err

    def run(self, host, port, debug, server):
        pass
