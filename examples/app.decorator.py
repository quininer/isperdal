#!/usr/bin/env python
# encoding: utf-8

from isperdal import microwave as u

app = u('/')

@app.all
def logger(this, req, res):
    print("logger {} {}".format(req.method, req.uri))

@app.get(u('index'))
def index(this, req, res):
    return res.ok("/INDEX")

@app.get(u('app/').all(
    lambda this, req, res: ('id' in req.session or (_ for _ in ()).throw(res.redirect('/index')))
))
def appindex(this, req, res):
    return res.ok("/APP/")

app.run()
