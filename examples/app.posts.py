#!/usr/bin/env python
# encoding: utf-8

from isperdal import Microwave as u
from database import db

app = u('/')
posts_node = app.then(u('posts/'))

@app.append(u('assets/'), u(':path'))
def assets(this, req, res):
    return res.file('/path/to/your', res.rest['path'])

@posts_node.get(u(':pid'))
def get_posts(this, req, res):
    body = (yield from db.query(req.rest['pid']).body)
    return res.ok(body)

@posts_node.append(u(':pid/'), u('comment'), methods=('POST',))
def add_comment(this, req, res):
    status = (yield from db.query(req.rest['pid']).update(req.body))
    return res.ok(status)

@posts_node.append(u(':pid/'), u('comment/'), u(':cid'), methods=('GET',))
def get_comment(this, req, res):
    comment = (yield from db.query(req.rest['pid']).query(req.rest['cid'].comment))
    return res.ok(comment)

app.run()
