#!/usr/bin/env python
# encoding: utf-8

from io import BytesIO
from functools import wraps
import asyncio

from isperdal.reqres import Request, Response
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


def aiotest(fn):
    @wraps(fn)
    def aio_wrap(*args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            asyncio.coroutine(fn)(*args, **kwargs)
        )
    return aio_wrap


def start_res(res_status, headers):
    assert isinstance(res_status, str)
    assert int(res_status.split()[0])
    assert isinstance(headers, type({}.items()))
    assert isinstance(list(headers)[0][1], str)
    assert isinstance(list(headers)[-1][-1], str)


class TestReq:
    @aiotest
    def test_body(self):
        req = Request(env)
        assert (yield from req.body).tell() is 0
        assert isinstance((yield from req.body).read(), bytes)

        req = Request(dict(env, **{
            'wsgi.input': fakeStreamIO(b"bar=baz")
        }))
        assert (yield from req.body).tell() is 0
        assert (yield from req.body).read() == b'bar=baz'
        assert (yield from req.env['wsgi.input'].read()) == b''
        assert (yield from req.body).tell() is 0

    @aiotest
    def test_rest(self):
        req = Request(env)
        assert (yield from req.rest('foo')) is None

        req._rest['foo'] = 'oof'
        assert (yield from req.rest('foo')) == 'oof'

        req._rest['中文'] = r'%E6%B5%8B%E8%AF%95'
        assert (yield from req.rest('中文')) == '测试'

    @aiotest
    def test_query(self):
        req = Request(env)
        assert (yield from req.query('foo')) is None

        req = Request(dict(env, **{
            'QUERY_STRING': "foo=one&foo=two&foo[foo]=three"
        }))
        assert (yield from req.query('foo')) == 'one'
        assert (yield from req.query('foo[foo]')) == 'three'

    @aiotest
    def test_header(self):
        req = Request(env)
        assert (yield from req.header('User-Agent')) == 'Mozilla'
        assert (yield from req.header('Remote-Addr')) == '127.0.0.1'

    @aiotest
    def test_from(self):
        req = Request(env)
        assert (yield from req.form('foo')) is None

        req = Request(dict(env, **{
            'REQUEST_METHOD': "POST",
            'CONTENT_TYPE': "application/x-www-form-urlencoded",
            'CONTENT_LENGTH': "30",
            'wsgi.input': fakeStreamIO(b"foo=one&foo=two&foo[foo]=three")
        }))
        assert (yield from req.form('foo')) == 'one'
        assert (yield from req.form('foo[foo]')) == 'three'

        req = Request(dict(env, **{
            'REQUEST_METHOD': "POST",
            'CONTENT_TYPE':
                "multipart/form-data; "
                "boundary=----WebKitFormBoundaryhvj9Daa5OwrBBWG9",
            'CONTENT_LENGTH': "382",
            'wsgi.input': fakeStreamIO(
                b'------WebKitFormBoundaryhvj9Daa5OwrBBWG9\r\n'
                b'Content-Disposition: '
                b'form-data; name="foo"; filename="test.txt"\r\n'
                b'Content-Type: text/plain\r\n\r\nHi\n\r\n'
                b'------WebKitFormBoundaryhvj9Daa5OwrBBWG9\r\n'
                b'Content-Disposition: form-data; name="bar"\r\n\r\nbaz\r\n'
                b'------WebKitFormBoundaryhvj9Daa5OwrBBWG9\r\n'
                b'Content-Disposition: form-data; '
                b'name="submit"\r\n\r\nUpload Image\r\n'
                b'------WebKitFormBoundaryhvj9Daa5OwrBBWG9--\r\n'
            )
        }))
        assert (yield from req.form('bar')) == 'baz'
        assert (yield from req.form('foo')) == b'Hi\n'


class TestRes:
    def setUp(self):
        self.res = Response(start_res)

    def test_status(self):
        assert self.res.status_code == 200
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

    def test_ok(self):
        result = self.res.header('X-Test', 'test too').ok()
        assert isinstance(result, Result)
        assert self.res.ok(True).ok()

    def test_err(self):
        assert self.res.err(True).err()
        try:
            raise self.res.err(True)
        except Err as err:
            assert err.err()

    def test_redirect(self):
        assert self.res.redirect(True).err()
        assert self.res.status_code == 302
