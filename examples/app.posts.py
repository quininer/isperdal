#!/usr/bin/env python
# encoding: utf-8

from isperdal import microwave as u

app = u('/')
posts_node = app.all(u('posts/'))

@app.get(u('assets/').all(u(':path')))
def assets(this, req, res):
    return res.file('/path/to/your', res.rest['path'])

@posts_node.get(u(':pid'))
def get_posts(this, req, res):
    body = (await db.query(req.rest['pid']).body)
    return res.ok(body)

@posts_node.post(u(':pid/').then(u('comment')))
def add_comment(this, req, res):
    status = (await db.query(req.rest['pid']).update(req.body))
    return res.ok(body)

@posts_node.get(u(':pid/').then(u('comment/').then(u(':cid'))))
def get_comment(this, req, res):
    comment = (await db.query(req.rest['pid']).query(req.rest['cid'].comment))
    return res.ok(comment)

app.all(posts_node)
app.run()
