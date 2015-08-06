import asyncio

from aiohttp.websocket import (
    MSG_PING,
    MSG_TEXT,
    MSG_BINARY,
    MSG_CLOSE
)


class WebSocket(object):
    def __init__(self):
        pass

    @asyncio.coroutine
    def __call__(self, req, res):
        self.req, self.res = req, res

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
                msg,
                (lambda: None)
            )()  # TODO argument

    def on_connect(self):
        pass

    def on_ping(self):
        # TODO
        self.writer.pong()

    def on_message(self, message):
        pass

    def on_close(self):
        pass
