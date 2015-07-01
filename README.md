isperdal
========

1. 优雅的路由分发
2. 良好的中间件支持
3. 状态友好的接口

Route
-----

以`/`分级触发

正常风格

    from isperdal import microwave as u

    # callback
    u('/').all(
        lambda this, req, res:
            res.ok("Hello world.")
    ).run()


    # decorator
    app = u('/')

    @app.all
    def foo(this: str, req: Request, res: Response):
        return res.ok("Hello world.")

    app.run()

----------

加点特技

    from isperdal import painting

    # callback
    '/'.all(
        lambda this, req, res:
            res.ok("Hello world.")
    ).run()


    # decorator
    app = '/'

    @app.all
    def foo(this: str, req: Request, res: Response):
        return res.ok("Hello world.")

    app.run()

----------

认为URL应该是一棵树，
对空中阁楼形式的URL不友好。

                 "/"
                 / \
                /   \
           assets/   posts/
            /  |       | \
           /   |       |  \
         img  css     (1  (2
                       X    \
                      / \    \
                      comment/  ---> POST
                    /     \    \
                  (1      (2    (1

----------

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

**完全不推荐使用无状态的REST**

**完全不打算支持正则URL**

Middleware
----------

基于分级的有序中间件，
非 wsgi 中间件，
本质上不区分 Middleware 与 APP。

[callback](/examples/app.callback.py)
[decorator](/examples/app.decorator.py)

Status
------

    app = u('/')

    @app.socket('/websocket')
    def socket(this, req, res):
        pass

    app.run()


But..
=====

看起来很美好？
实际上只是个设想，说不定哪天 Rust 的官方`async IO`出来了就改用 Rust 了。
