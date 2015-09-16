from asyncio import get_event_loop
from ssl import SSLContext
from sys import version_info

if version_info > (3, 3, 0):
    from ssl import PROTOCOL_TLSv1_2 as PROTOCOL
else:
    from ssl import PROTOCOL_TLSv1_1 as PROTOCOL

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
            environ['websocket.reader'] = self.reader
            environ['websocket.writer'] = writer
            environ['websocket.parser'] = parser
            environ['websocket.protocol'] = protocol

        return environ


class AioHTTPServer(object):
    def __init__(self, host, port, debug, ssl):
        self.host = host
        self.port = port
        self.debug = debug
        if ssl:
            self.ssl = SSLContext(PROTOCOL)
            self.ssl.load_cert_chain(*ssl)
        else:
            self.ssl = None

    def run(self, handler):
        loop = get_event_loop()

        loop.run_until_complete(
            loop.create_server(
                lambda: AioWSGIServerProtocol(
                    handler,
                    readpayload=False,
                    debug=self.debug,
                    is_ssl=bool(self.ssl)
                ),
                self.host,
                self.port,
                ssl=self.ssl
            )
        )

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            loop.stop()
