#!/usr/bin/env python
# encoding: utf-8

from isperdal import Node as u

root = u('/')

@root.append(u(":name") / u(":id"))
async def foo(this, req, res):
    return res.push(
        "{} {}".format(
            await req.rest("name"),
            await req.rest("id")
        )
    ).ok()

root.run()
