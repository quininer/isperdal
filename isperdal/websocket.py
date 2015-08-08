import asyncio
from functools import partial

from aiohttp.websocket import (
    MSG_PING,
    MSG_TEXT,
    MSG_BINARY,
    MSG_CLOSE
)

from .utils import Ok, Err


class WebSocket(object):
    def __init__(self, node, req, res):
        self.node = node
        self.req = req
        self.res = res

    def close(self):
        raise Err('close')

    @asyncio.coroutine
    def __call__(self):

        while True:
            try:
                # TODO self.wsqueue
                msg = yield from self.wsqueue.read()
            except:
                # client dropped connection
                break

            try:
                yield from partial({
                    MSG_PING: self.on_ping,
                    MSG_TEXT: self.on_message,
                    MSG_BINARY: self.on_message,
                    MSG_CLOSE: self.on_close
                }.get(
                    msg.tp,
                    asyncio.coroutine(lambda: None)
                ), *{
                    MSG_TEXT: [msg.data],
                    MSG_BINARY: [msg.data]
                }.get(
                    msg.tp,
                    []
                ))()

            except Err as err:
                if err.err() == 'close':
                    break

    @asyncio.coroutine
    def on_handshake(self):
        self.res.start_response(
            self.res.status_code or self.req.env['websocket.status'],
            self.res.headers.items() or self.req.env['websocket.headers']
        )

        self.wsqueue = self.req.env['websocket.reader'].set_parser(
            self.req.env['websocket.parser']
        )

    @asyncio.coroutine
    def on_connect(self):
        pass

    @asyncio.coroutine
    def on_ping(self):
        # TODO
        self.writer.pong()

    @asyncio.coroutine
    def on_message(self, message):
        pass

    @asyncio.coroutine
    def on_close(self):
        pass
