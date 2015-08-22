#!/usr/bin/env python
# encoding: utf-8

from asyncio import coroutine

from aiohttp.websocket import (
    MSG_PING,
    MSG_TEXT,
    MSG_BINARY,
    MSG_CLOSE
)

from isperdal.utils import aiotest
from isperdal.websocket import WebSocket


class fakeWriter:
    def send(self, data):
        assert data == "MSG"

    def pong(self):
        pass


class fakeWsqueue:
    event = list(map(type('fakeMessage', (), {
        '__init__': (
            lambda self, msg:
                setattr(self, 'tp', msg) or setattr(self, 'data', "MSG")
        )
    }), [MSG_PING, MSG_TEXT, MSG_BINARY, MSG_CLOSE]))
    num = 0

    @coroutine
    def read(self):
        self.num += 1
        return self.event[self.num-1]


class fakeReader:
    def set_parser(self, parser):
        assert parser == "PARSER"
        return fakeWsqueue()


class fakeReq:
    env = {
        'websocket.status': 101,
        'websocket.headers': "HEADERS",
        'websocket.reader': fakeReader(),
        'websocket.writer': fakeWriter(),
        'websocket.parser': "PARSER",
        'websocket.protocol': None
    }


class fakeRes:
    hook = []
    status_code = 0
    headers = {}

    def start_response(self, status, headers):
        assert status == "101 Switching Protocols"
        assert headers == "HEADERS"


class WS(WebSocket):
    @coroutine
    def on_handshake(self):
        result = yield from super().on_handshake()
        assert result is None

    @coroutine
    def on_connect(self):
        assert True

    @coroutine
    def on_ping(self):
        result = self.pong()
        assert result is None

    @coroutine
    def on_message(self, message):
        assert message == "MSG"
        self.send(message)

    @coroutine
    def on_close(self):
        result = self.close()
        assert result is True


class TestWs:
    def setUp(self):
        self.req, self.res = fakeReq(), fakeRes()
        self.ws = WS(None, self.req, self.res)

    @aiotest
    def test_call(self):
        yield from self.ws()
