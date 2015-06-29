#!/usr/bin/env python
# encoding: utf-8

from isperdal import microwave as u

u('/').all(lambda this, req, res: print("logger {} {}".format(req.method, req.uri)))
    .get(u('index'))(lambda this, req, res: (await res.push("INDEX")))
    .get(u('app/').all(
        lambda this, req, res: ('id' in req.session or (await res.redirect('/index')))
    ))(lambda this, req, res: (await res.push("/APP/")))
    .run()
