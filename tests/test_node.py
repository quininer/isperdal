#!/usr/bin/env python
# encoding: utf-8

from copy import copy

from isperdal import Node as u
from isperdal.request import Request
from isperdal.response import Response
from isperdal.websocket import WebSocket
from isperdal.utils import unok, aiotest

env = {
    'REQUEST_METHOD': "GET",
    'PATH_INFO': "/"
}


def start_response(res_status, headers):
    assert isinstance(res_status, str)
    assert isinstance(headers, type({}.items()))


class TestNode:
    def setUp(self):
        self.root = u('/')

    @aiotest
    def test_route(self):
        index = u('index')
        self.root.route(index)(lambda: 1)
        assert not self.root.subnode[-1].handles['OPTION']
        assert self.root.subnode[-1].handles['HEAD']
        assert (yield from self.root.subnode.pop().handles['GET'].pop()()) is 1

        self.root.route(index)(WebSocket)
        assert not self.root.subnode[-1].handles['OPTION']
        assert self.root.subnode[-1].handles['HEAD']
        assert issubclass(
            self.root.subnode.pop().handles['GET'].pop(),
            WebSocket
        )

        self.root.route(
            index, methods=('OPTION',)
        )(lambda: 1)
        assert (
            yield from self.root.subnode.pop().handles['OPTION'].pop()()
        ) is 1

    @aiotest
    def test_all(self):
        self.root.all()(lambda: 1)
        assert self.root.handles['OPTION']
        assert self.root.handles['GET']

        for h in self.root.handles.keys():
            assert (yield from self.root.handles[h].pop()()) is 1

        self.root.all(('GET',))(lambda: 1)
        assert not self.root.handles['OPTION']
        assert (yield from self.root.handles['GET'].pop()()) is 1

        self.root.all()((lambda: 1), (lambda: 2))
        assert (yield from self.root.handles['GET'].pop()()) is 2
        assert (yield from self.root.handles['GET'].pop()()) is 1

    @aiotest
    def test_add(self):
        index = u('index/').all()(lambda: 1)
        self.root.add(index)
        assert (yield from self.root.subnode[0].handles['GET'].pop()()) is 1
        index2 = u('index/').get(u('app'))(lambda: 2)
        self.root.add(index2)
        assert (
            yield from self.root
            .subnode.pop()
            .subnode.pop()
            .handles['GET'].pop()()
        ) is 2

    @aiotest
    def test_then(self):
        self.root.then(u('index/')).then(u('test')).all()(lambda: 1)
        assert (
            yield from self.root
            .subnode.pop()
            .subnode.pop()
            .handles['GET'].pop()()
        ) is 1

    @aiotest
    def test_append(self):
        self.root.append([u('index/'), u('test')])(lambda: 1)
        assert (
            yield from self.root
            .subnode.pop()
            .subnode.pop()
            .handles['GET'].pop()()
        ) is 1

        self.root.append([u('index/'), u('test')], methods=('GET',))(lambda: 1)
        assert not self.root.subnode[-1].subnode[-1].handles['OPTION']
        assert (
            yield from self.root
            .subnode.pop()
            .subnode.pop()
            .handles['GET'].pop()()
        ) is 1

    @aiotest
    def test_get(self):
        self.root.get(u('index/'))(lambda: 1)
        assert not self.root.subnode[-1].handles['OPTION']
        assert not self.root.subnode[-1].handles['HEAD']
        assert (yield from self.root.subnode.pop().handles['GET'].pop()()) is 1

    @aiotest
    def test_err(self):
        self.root.err(200)(lambda: 1)
        assert (yield from self.root.codes.pop(200)()) is 1

    @aiotest
    def test_handler(self):
        # '/'
        req, res = Request(env), Response(start_response)
        assert req.branches.pop(0) == '/'

        result = u('/').all()(
            lambda this, req, res:
                res.push("Test.").ok()
        ).handler(req, res, copy(req.branches))

        assert (yield from unok(result)) == [b'Test.']

        # '/posts/q'
        env['PATH_INFO'] = '/posts/1'
        req, res = Request(env), Response(start_response)
        assert req.branches.pop(0) == '/'

        result = u('/').append([u('posts/'), u(':id')])(
            lambda this, req, res:
                res.push((yield from req.rest('id'))).ok()
        ).handler(req, res, copy(req.branches))

        assert (yield from unok(result)) == [b'1']

        # '/file/img/test.png'
        env['PATH_INFO'] = '/file/img/test.png'
        req, res = Request(env), Response(start_response)
        assert req.branches.pop(0) == '/'

        result = u('/').append([u('file/'), u('img/'), u(':!png')])(
            lambda this, req, res:
                res.push((yield from req.rest('png'))).ok()
        ).handler(req, res, copy(req.branches))

        assert (yield from unok(result)) == [b'test.png']

        # '/error'
        env['PATH_INFO'] = '/error'
        req, res = Request(env), Response(start_response)
        assert req.branches.pop(0) == '/'

        result = u('/').err(500)(
            lambda this, req, res, err:
                res.push(err).ok()
        ).all()(
            lambda this, req, res:
                res.status(500).err("Test")
        ).handler(req, res, copy(req.branches))

        assert (yield from unok(result)) == [b'Test']

    def test_copy(self):
        node = u("node")
        node.subnode = 1
        node.handles = 2
        node.codes = 3

        node_copy = node.copy("node/")

        assert node_copy == "node/"
        assert node_copy.subnode == node.subnode
        assert node_copy.handles == node.handles
        assert node_copy.codes == node.codes

    def test_div(self):
        nodes = u("/") / u("name")
        nodes2 = u("/") / u("name") / u("id")

        assert nodes == ["/", "name"]
        assert nodes2 == ["/", "name/", "id"]
