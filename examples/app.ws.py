#!/usr/bin/env python
# encoding: utf-8

import asyncio

from isperdal import Microwave as u
from isperdal.websocket import WebSocket

app = u('/')


@app.all()
class Ws(WebSocket):
    @asyncio.coroutine
    def on_message(self, message):
        self.send(message)

app.run()
