#!/usr/bin/env python
# encoding: utf-8

from isperdal import Node as u

app = u('/')


@app.get(*map(u, ('', "index")))
async def index(this, req, res):
    return res.push(
        await req.query("id")
    ).ok()


app.run()
