#!/usr/bin/env python
# encoding: utf-8

from isperdal import Node as u
from isperdal import only

app = u('/')


@app.get(*map(u, ('', "index")))
@only
async def index(this, req, res):
    return res.push(
        await req.query("id")
    ).ok()


app.run()
