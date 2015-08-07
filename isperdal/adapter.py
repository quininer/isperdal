import asyncio

from aiohttp.wsgi import WSGIServerHttpProtocol
from aiohttp.websocket import do_handshake


class AioWSGIServerProtocol(WSGIServerHttpProtocol):
    def create_wsgi_environ(self, message, payload):
        environ = super().create_wsgi_environ(message, payload)

        if 'websocket' in message.headers.get('UPGRADE', '').lower():
            # websocket handshake
            status, headers, parser, writer, protocol = do_handshake(
                message.method, message.headers, self.transport
            )
            environ['websocket'] = True
            environ['websocket.status'] = status
            environ['websocket.headers'] = headers
            environ['websocket.writer'] = writer
            environ['websocket.parser'] = parser
            environ['websocket.version'] = protocol

        return environ


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
