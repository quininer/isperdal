#!/usr/bin/env python
# encoding: utf-8

from isperdal import Microwave as u
from database import db
from os import path

app = u('/')
posts_node = app.then(u('posts/'))

@app.append(u('assets/'), u(':!path'))
def assets(this, req, res):
    return res.file(path.join('/path/to/your', res.rest['path']))

@posts_node.get(u(':pid'))
def get_posts(this, req, res):
    body = (yield from db.query(req.rest['pid']).body)
    return res.push(body).ok()

@posts_node.append(u(':pid/'), u('comment'), methods=('POST',))
def add_comment(this, req, res):
    status = (yield from db.query(req.rest['pid']).update(req.body))
    return res.push(status).ok()

@posts_node.append(*map(u, [':pid/', 'comment/', ':cid']), methods=('GET',))
def get_comment(this, req, res):
    comment = (yield from db.query(req.rest['pid']).query(req.rest['cid'].comment))
    return res.push(comment).ok()

app.run()
