#!/usr/bin/env python
# encoding: utf-8

from isperdal import Microwave as u

app = u('/')


@app.get(u(":id"))
async def index(this, req, res):
    return res.push(
        await req.rest("id")
    ).ok()


app.run()
