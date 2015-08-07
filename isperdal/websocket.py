import asyncio

from aiohttp.websocket import (
    MSG_PING,
    MSG_TEXT,
    MSG_BINARY,
    MSG_CLOSE
)


class WebSocket(object):
    def __init__(self, req, res):
        self.req = req
        self.res = res

    @asyncio.coroutine
    def __call__(self):

        while True:
            try:
                # TODO self.wsqueue
                msg = yield from self.wsqueue.read()
            except:
                # client dropped connection
                break

            yield from {
                MSG_PING: self.on_ping,
                MSG_TEXT: self.on_message,
                MSG_BINARY: self.on_message,
                MSG_CLOSE: self.on_close
            }.get(
                # TODO msg type?
                int(msg),
                (lambda: None)
            )()  # TODO argument

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
