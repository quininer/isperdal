#!/usr/bin/env python
# encoding: utf-8

from io import BytesIO
from functools import wraps
import asyncio

from isperdal.request import Request


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


class TestReq:
    @aiotest
    def test_body(self):
        req = Request(env)
        assert (yield from req.body()).tell() is 0
        assert isinstance((yield from req.body()).read(), bytes)

        req = Request(dict(env, **{
            'wsgi.input': fakeStreamIO(b"bar=baz")
        }))
        assert (yield from req.body()).tell() is 0
        assert (yield from req.body()).read() == b'bar=baz'
        assert (yield from req.env['wsgi.input'].read()) == b''
        assert (yield from req.body()).tell() is 0

    @aiotest
    def test_rest(self):
        req = Request(env)
        assert (yield from req.rest('foo')) is None

        req._rest['foo'] = 'oof'
        assert (yield from req.rest('foo')) == 'oof'

        req._rest['中文'] = r'%E6%B5%8B%E8%AF%95'
        assert (yield from req.rest('中文')) == '测试'

    @aiotest
    def test_querys(self):
        req = Request(env)
        assert dict((yield from req.querys())) == {}

        req = Request(dict(env, **{
            'QUERY_STRING': "foo=one&foo=two&foo[foo]=three"
        }))
        assert (yield from req.querys()).get('foo') == ['one', 'two']
        assert (yield from req.querys()).get('foo[foo]') == ['three']

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
    def test_forms(self):
        req = Request(env)
        assert dict((yield from req.forms())) == {}

        req = Request(dict(env, **{
            'REQUEST_METHOD': "POST",
            'CONTENT_TYPE': "application/x-www-form-urlencoded",
            'CONTENT_LENGTH': "30",
            'wsgi.input': fakeStreamIO(b"foo=one&foo=two&foo[foo]=three")
        }))
        assert (yield from req.forms()).getvalue('foo') == ['one', 'two']
        assert (yield from req.forms()).getvalue('foo[foo]') == 'three'

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
        assert (yield from req.forms()).getvalue('bar') == 'baz'
        assert (yield from req.forms()).getvalue('foo') == b'Hi\n'

    @aiotest
    def test_form(self):
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
