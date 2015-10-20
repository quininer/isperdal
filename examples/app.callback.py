#!/usr/bin/env python
# encoding: utf-8

from isperdal import Microwave as u


u('/').all()(
    lambda this, req, res:
        print("logger {} {}".format(req.method, req.uri))

).get(u(""), u('index'))(
    lambda this, req, res:
        res.push("INDEX").ok()

).get(
    u('app/').all()(
        lambda this, req, res:
            (yield from req.query('id')) == 'isperdal' or
            (_ for _ in ()).throw(res.status(302).err('/index'))
    )
)(
    lambda this, req, res:
        res.push("/APP/").ok()
).run()
