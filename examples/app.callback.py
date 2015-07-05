#!/usr/bin/env python
# encoding: utf-8

from isperdal import Microwave as u

u('/').all(lambda this, req, res: print("logger {} {}".format(req.method, req.uri)))\
    .get(u(""), u('index'))(lambda this, req, res: res.push("INDEX"))\
    .get(u('app/').all(
        lambda this, req, res: ('id' in req.session or (_ for _ in ()).throw(res.redirect('/index')))
    ))(lambda this, req, res: res.push("/APP/"))\
    .run()
