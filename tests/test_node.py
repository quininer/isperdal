#!/usr/bin/env python
# encoding: utf-8

from isperdal import Microwave as u
from isperdal.reqres import Request, Response
from isperdal.utils import Result

env = {
    'REQUEST_METHOD': 'GET',
    'PATH_INFO': '/'
}
def start_res(res_status, headers):
    assert isinstance(res_status, str)
    assert isinstance(headers, list)

class TestNode:
    def setUp(self):
        self.root = u('/')

    def test_route(self):
        index = u('index')
        self.root.route(index)(lambda: True)
        assert not self.root.subnode[-1].handles['OPTION']
        assert self.root.subnode[-1].handles['HEAD']
        assert self.root.subnode.pop().handles['GET'].pop()()

        self.root.route(index, methods=('OPTION',))(lambda: True)
        assert self.root.subnode.pop().handles['OPTION'].pop()()

    def test_all(self):
        self.root.all(lambda: True)
        assert self.root.handles['OPTION']
        assert self.root.handles['GET']

        for h in self.root.handles.keys():
            assert self.root.handles[h].pop()()

        self.root.all((lambda: True), methods=('GET',))
        assert not self.root.handles['OPTION']
        assert self.root.handles['GET'].pop()()

    def test_add(self):
        index = u('index/').all(lambda: True)
        self.root.add(index)
        assert self.root.subnode.pop().handles['GET'].pop()()

    def test_then(self):
        self.root.then(u('index/')).then(u('test')).all(lambda: True)
        assert self.root.subnode.pop().subnode.pop().handles['GET'].pop()

    def test_append(self):
        self.root.append(u('index/'), u('test'))(lambda: True)
        assert self.root.subnode.pop().subnode.pop().handles['GET'].pop()

        self.root.append(u('index/'), u('test'), methods=('GET',))(lambda: 1)
        assert not self.root.subnode[-1].subnode[-1].handles['OPTION']
        assert self.root.subnode.pop().subnode.pop().handles['GET'].pop()

    def test_get(self):
        self.root.get(u('index/'))(lambda: True)
        assert not self.root.subnode[-1].handles['OPTION']
        assert not self.root.subnode[-1].handles['HEAD']
        assert self.root.subnode.pop().handles['GET'].pop()()

    def test_err(self):
        self.root.err(200)(lambda: True)
        assert self.root.codes.pop(200)()

    def test_handler(self):
        req, res = Request(env), Response(start_res)
        assert req.next.pop(0) == '/'
        result = u('/').all(
            lambda this, req, res:
                res.push("Test.").ok()
        )._Microwave__handler(req, res)

        assert isinstance(result, Result)
        assert result.ok()

        env['PATH_INFO'] = '/posts/1'
        req, res = Request(env), Response(start_res)
        assert req.next.pop(0) == '/'
        result = u('/').append(u('posts/'), u(':id'))(
            lambda this, req, res:
                res.push(req.rest('id')).ok()
        )._Microwave__handler(req, res)
        assert result.ok() == [b'1']

        env['PATH_INFO'] = '/file/img/test.png'
        req, res = Request(env), Response(start_res)
        assert req.next.pop(0) == '/'
        result = u('/').append(u('file/'), u('img/'), u(':!png'))(
            lambda this, req, res:
                res.push(req.rest('png')).ok()
        )._Microwave__handler(req, res)
        assert result.ok() == [b'test.png']

        env['PATH_INFO'] = '/error'
        req, res = Request(env), Response(start_res)
        assert req.next.pop(0) == '/'
        result = u('/').err(500)(
            lambda this, req, res, err:
                res.push(err).ok()
        ).all(
            lambda this, req, res:
                res.status(500).err("Test")
        )._Microwave__handler(req, res)
        assert result.ok() == [b'Test']