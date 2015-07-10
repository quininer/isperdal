#!/usr/bin/env python
# encoding: utf-8

from isperdal.reqres import Request, Response
from isperdal.utils import Result, Err
from io import BytesIO


env = {
    'REQUEST_METHOD': "GET",
    'PATH_INFO': "/",
    'RAW_URI': "/",
    'QUERY_STRING': "",
    'wsgi.input': BytesIO(),
    'HTTP_USER_AGENT': "Mozilla",
    'REMOTE_ADDR': "127.0.0.1"
}


def start_res(res_status, headers):
    assert isinstance(res_status, str)
    assert int(res_status.split()[0])
    assert isinstance(headers, list)
    assert isinstance(headers[0][1], str)
    assert isinstance(headers[-1][-1], str)


class TestReq:
    def test_body(self):
        req = Request(env)
        assert req.body.tell() is 0
        assert isinstance(req.body.read(), bytes)

        req = Request(dict(env, **{
            'wsgi.input': BytesIO(b"bar=baz")
        }))
        assert req.body.tell() is 0
        assert req.body.read() == b'bar=baz'
        assert req.env['wsgi.input'].tell() == 7
        assert req.body.tell() is 0

    def test_rest(self):
        req = Request(env)
        assert req.rest('foo') is None

        req._rest['foo'] = 'oof'
        assert req.rest('foo') == 'oof'

    def test_query(self):
        req = Request(env)
        assert req.query('foo') is None

        req = Request(dict(env, **{
            'QUERY_STRING': "foo=one&foo=two&foo[foo]=three"
        }))
        assert req.query('foo') == 'two'
        assert req.query('foo[foo]') == 'three'

    def test_header(self):
        req = Request(env)
        assert req.header('User-Agent') == 'Mozilla'
        assert req.header('Remote-Addr') == '127.0.0.1'

    def test_from(self):
        req = Request(env)
        assert req.form('foo') is None

        req = Request(dict(env, **{
            'REQUEST_METHOD': "POST",
            'CONTENT_TYPE': "application/x-www-form-urlencoded",
            'CONTENT_LENGTH': "30",
            'wsgi.input': BytesIO(b"foo=one&foo=two&foo[foo]=three")
        }))
        assert req.form('foo') == 'one'
        assert req.form('foo[foo]') == 'three'

        req = Request(dict(env, **{
            'REQUEST_METHOD': "POST",
            'CONTENT_TYPE':
                "multipart/form-data; "
                "boundary=----WebKitFormBoundaryhvj9Daa5OwrBBWG9",
            'CONTENT_LENGTH': "382",
            'wsgi.input': BytesIO(
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
        assert req.form('bar') == 'baz'
        assert req.form('foo') == b'Hi\n'


class TestRes:
    def setUp(self):
        self.res = Response(start_res)

    def test_status(self):
        assert self.res.status_code == 200
        assert self.res.status(500) is self.res
        assert self.res.status_code == 500

    def test_header(self):
        assert not self.res.headers
        assert self.res.header('X-Test', 'test too') is self.res
        assert self.res.headers['X-Test'] == 'test too'

    def test_push(self):
        assert not self.res.body
        assert self.res.push('push') is self.res
        assert self.res.body[-1] == b'push'

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
