import asyncio

from aiohttp.wsgi import WSGIServerHttpProtocol
from aiohttp.websocket import do_handshake


class AioWSGIServerProtocol(WSGIServerHttpProtocol):
    @asyncio.coroutine
    def handle_request(self, message, payload):
        if 'websocket' in message.headers.get('UPGRADE', "").lower():

            # websocket handshake
            status, headers, parser, writer, protocol = do_handshake(
                message.method,
                message.headers,
                self.transport
            )

            pass
        else:
            yield from super().handle_request(message, payload)


class AioHTTPServer(object):
    def __init__(self, host, port, debug, ssl):
        self.host = host
        self.port = port
        self.debug = debug
        self.ssl = ssl

    def run(self, handler):

        loop = asyncio.get_event_loop()

        loop.run_until_complete(
            loop.create_server(
                lambda: AioWSGIServerProtocol(
                    handler,
                    readpayload=False,
                    debug=self.debug,
                    is_ssl=self.ssl
                ),
                self.host,
                self.port
            )
        )

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            loop.stop()
