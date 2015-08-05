import asyncio

from aiohttp.websocket import (
    MSG_PING,
    MSG_TEXT,
    MSG_BINARY,
    MSG_CLOSE
)


class WebSocket(object):
    def __init__(self, ):
        pass

    @asyncio.coroutine
    def __call__(self, req, res):
        while True:
            try:
                msg = yield from self.wsqueue.read()
            except:
                # client dropped connection
                break
            {
                MSG_PING: self.on_ping,
                MSG_TEXT: self.on_message,
                MSG_BINARY: self.on_message,
                MSG_CLOSE: self.on_close
            }.get(
                msg,
                (lambda: None)
            )()

    def on_connect(self, req, res):
        pass

    def on_close(self):
        pass

    def on_ping(self):
        pass

    def on_message(self):
        pass
