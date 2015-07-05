class ServerAdapter(object):
    def __init__(self, host, port, debug):
        self.host = host
        self.port = port
        self.debug = debug

    def run(self, handler):
        pass

class AioHTTPServerAdapter(ServerAdapter):
    def run(self, handler):
        import asyncio
        from aiohttp.wsgi import WSGIServerHttpProtocol

        loop = asyncio.get_event_loop()

        loop.run_until_complete(
            loop.create_server(
                lambda: WSGIServerHttpProtocol(handler, readpayload=True, debug=self.debug),
                self.host,
                self.port
            )
        )

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            loop.stop()

class PulsarServerAdapter(ServerAdapter):
    def run(self, handler):
        from pulsar.apps import wsgi
        wsgi.WSGIServer(callable=handler).start()

adapter = {
    'aiohttp': AioHTTPServerAdapter,
    'pulsar': PulsarServerAdapter
}
