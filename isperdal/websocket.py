from asyncio import coroutine
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
        self.node = node
        self.req = req
        self.res = res
        self.status = req.env['websocket.status']
        self.headers = req.env['websocket.headers']
        self.reader = req.env['websocket.reader']
        self.writer = req.env['websocket.writer']
        self.parser = req.env['websocket.parser']
        self.protocol = req.env['websocket.protocol']

    def send(self, data):
        self.writer.send(data)

    def pong(self):
        self.writer.pong()

    def close(self):
        raise Close()

    @coroutine
    def __call__(self):
        yield from self.on_handshake()
        yield from self.on_connect()

        while True:
            try:
                message = yield from self.wsqueue.read()
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
                        message.tp,
                        coroutine(lambda: None)
                    ),

                    *{
                        MSG_TEXT: [message.data],
                        MSG_BINARY: [message.data]
                    }.get(message.tp, [])
                )()

            except Close:
                break

        return

    @coroutine
    def on_handshake(self):
        for fn in self.res.hook:
            fn(self.res)
        self.res.start_response(
            resp_status(self.res.status_code or self.status),
            self.res.headers.items() or self.headers
        )

        self.wsqueue = self.reader.set_parser(self.parser)

    @coroutine
    def on_connect(self):
        pass

    @coroutine
    def on_ping(self):
        self.pong()

    @coroutine
    def on_message(self, message):
        pass

    @coroutine
    def on_close(self):
        self.close()
