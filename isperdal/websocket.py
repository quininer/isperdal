import asyncio
from functools import partial

from aiohttp.websocket import (
    MSG_PING,
    MSG_TEXT,
    MSG_BINARY,
    MSG_CLOSE
)

from .utils import resp_status


class Close(StopIteration):
    pass


class WebSocket(object):
    def __init__(self, node, req, res):
        print("WS init")
        self.node = node
        self.req = req
        self.res = res
        self.status = req.env['websocket.status']
        self.headers = req.env['websocket.headers']
        self.reader = req.env['websocket.reader']
        self.writer = req.env['websocket.writer']
        self.parser = req.env['websocket.parser']
        self.version = req.env['websocket.version']

    def close(self):
        raise Close()

    @asyncio.coroutine
    def __call__(self):
        yield from self.on_handshake()
        yield from self.on_connect()

        while True:
            try:
                msg = yield from self.wsqueue.read()
            except:
                # client dropped connection
                break

            try:
                yield from partial(
                    {
                        MSG_PING: self.on_ping,
                        MSG_TEXT: self.on_message,
                        MSG_BINARY: self.on_message,
                        MSG_CLOSE: self.on_close
                    }.get(
                        msg.tp,
                        asyncio.coroutine(lambda: None)
                    ),

                    *{
                        MSG_TEXT: [msg.data],
                        MSG_BINARY: [msg.data]
                    }.get(
                        msg.tp,
                        []
                    )
                )()

            except Close:
                break

    @asyncio.coroutine
    def on_handshake(self):
        self.res.start_response(
            resp_status(self.res.status_code or self.status),
            self.res.headers.items() or self.headers
        )

        self.wsqueue = self.reader.set_parser(
            self.parser
        )

    @asyncio.coroutine
    def on_connect(self):
        pass

    @asyncio.coroutine
    def on_ping(self):
        self.writer.pong()

    @asyncio.coroutine
    def on_message(self, message):
        pass

    @asyncio.coroutine
    def on_close(self):
        pass
