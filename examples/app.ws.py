#!/usr/bin/env python
# encoding: utf-8

from aysncio import coroutine

from isperdal import Node as u
from isperdal.websocket import WebSocket

app = u('/')


@app.all()
class Ws(WebSocket):
    @coroutine
    def on_message(self, message):
        self.send(message)

app.run()
