#!/usr/bin/env python
# encoding: utf-8

from io import BytesIO
import asyncio

from isperdal.response import Response
from isperdal.utils import Result, Err


class fakeStreamIO():
    def __init__(self, buffer=b''):
        self.buffer = BytesIO(buffer)

    @asyncio.coroutine
    def read(self):
        return self.buffer.read()


env = {
    'REQUEST_METHOD': "GET",
    'PATH_INFO': "/",
    'RAW_URI': "/",
    'QUERY_STRING': "",
    'wsgi.input': fakeStreamIO(),
    'HTTP_USER_AGENT': "Mozilla",
    'REMOTE_ADDR': "127.0.0.1"
}


def start_response(res_status, headers):
    assert isinstance(res_status, str)
    assert int(res_status.split()[0])
    assert isinstance(headers, type({}.items()))
    assert isinstance(list(headers)[0][1], str)
    assert isinstance(list(headers)[-1][-1], str)


class TestRes:
    def setUp(self):
        self.res = Response(start_response)

    def test_status(self):
        assert self.res.status_code == 0
        assert self.res.status(500) is self.res
        assert self.res.status_code == 500
        assert self.res.status_text is None
        assert self.res.status(418, "I\"m a teapot") is self.res
        assert self.res.status_text == "I\"m a teapot"

    def test_header(self):
        assert not self.res.headers
        assert self.res.header('X-Test', 'test too') is self.res
        assert self.res.headers['X-Test'] == 'test too'

    def test_push(self):
        assert not self.res.body
        assert self.res.push('push') is self.res
        assert self.res.body[-1] == b'push'

        assert self.res.push('p'*8193) is self.res
        assert self.res.body[-2] == b'p'*8192
        assert self.res.body[-1] == b'p'

    def test_hook(self):
        assert self.res.hook(lambda res: res) is self.res
        assert self.res.hooks[-1](self.res) is self.res

    def test_ok(self):
        assert self.res.done is False
        result = self.res.header('X-Test', 'test too').ok()
        assert self.res.done is True
        assert isinstance(result, Result)
        assert self.res.ok(True).ok()

    def test_err(self):
        assert self.res.err(True).err()
        try:
            raise self.res.err(True)
        except Err as err:
            assert err.err()
