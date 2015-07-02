class Ok(object):
    pass

class Err(Exception):
    pass

class Request(object):

    headers = {}

    def __init__(self):
        pass

class Response(object):

    headers = {}

    def __init__(self):
        pass

class Microwave(str):
    """
    Microwave.
    """

    nodes = []

    def __init__(self, node):
        pass

    def route(self):
        pass

    def all(self):
        pass

    def head(self):
        pass

    def get(self):
        pass

    def post(self):
        pass

    def err(self):
        pass

    def run(self):
        pass
