class ServerAdapter(object):
    def __init__(self, host: str="127.0.0.1", port: int=8000, debug: bool=True):
        self.host = host
        self.port = port
        self.debug = debug

    def run(self, handler):
        pass

class AioHTTPServerAdapter(ServerAdapter):
    def run(self, handler):
        import asyncio
        from aiohttp.wsgi import WSGIServerHttpProtocol

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

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

adapter = {
    'aiohttp': AioHTTPServerAdapter
}
