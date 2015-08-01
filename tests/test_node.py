#!/usr/bin/env python
# encoding: utf-8

import asyncio
from functools import wraps

from isperdal import Microwave as u
from isperdal.reqres import Request, Response
from isperdal.utils import Ok

env = {
    'REQUEST_METHOD': "GET",
    'PATH_INFO': "/"
}


def aiotest(fn):
    @wraps(fn)
    def aio_wrap(*args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            asyncio.coroutine(fn)(*args, **kwargs)
        )
        # loop.run_forever()
        # loop.stop()
    return aio_wrap


def start_res(res_status, headers):
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
        assert (yield from self.root.subnode.pop().handles['GET'].pop()()) is 1

    @aiotest
    def test_then(self):
        self.root.then(u('index/')).then(u('test')).all()(lambda: 1)
        assert (
            yield from self.root.
            subnode.pop().subnode.pop().
            handles['GET'].pop()()
        ) is 1

    @aiotest
    def test_append(self):
        self.root.append(u('index/'), u('test'))(lambda: 1)
        assert (
            yield from self.root.
            subnode.pop().subnode.pop().
            handles['GET'].pop()()
        ) is 1

        self.root.append(u('index/'), u('test'), methods=('GET',))(lambda: 1)
        assert not self.root.subnode[-1].subnode[-1].handles['OPTION']
        assert (
            yield from self.root.
            subnode.pop().subnode.pop().
            handles['GET'].pop()()
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
        req, res = Request(env), Response(start_res)
        assert req.next.pop(0) == '/'

        result = u('/').all()(
            lambda this, req, res:
                res.push("Test.").ok()
        )._Microwave__handler(req, res)

        assert (yield from u.unok(result)) == [b'Test.']

        # '/posts/q'
        env['PATH_INFO'] = '/posts/1'
        req, res = Request(env), Response(start_res)
        assert req.next.pop(0) == '/'

        result = u('/').append(u('posts/'), u(':id'))(
            lambda this, req, res:
                res.push((yield from req.rest('id')))
        )._Microwave__handler(req, res)

        assert (yield from u.unok(result)) == [b'1']

        # '/file/img/test.png'
        env['PATH_INFO'] = '/file/img/test.png'
        req, res = Request(env), Response(start_res)
        assert req.next.pop(0) == '/'

        result = u('/').append(u('file/'), u('img/'), u(':!png'))(
            lambda this, req, res:
                res.push((yield from req.rest('png'))).ok()
        )._Microwave__handler(req, res)

        assert (yield from u.unok(result)) == [b'test.png']

        # '/error'
        env['PATH_INFO'] = '/error'
        req, res = Request(env), Response(start_res)
        assert req.next.pop(0) == '/'

        result = u('/').err(500)(
            lambda this, req, res, err:
                res.push(err).ok()
        ).all()(
            lambda this, req, res:
                res.status(500).err("Test")
        )._Microwave__handler(req, res)

        assert (yield from u.unok(result)) == [b'Test']

    @aiotest
    def test_unok(self):
        assert (
            yield from u.unok(asyncio.coroutine(lambda: Ok(True))())
        ) is True
        assert (
            yield from u.unok(asyncio.coroutine(lambda: Ok(False))())
        ) is False
