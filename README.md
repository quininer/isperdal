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
            (await res.push("Hello world."))
    ).run()


    # decorator
    app = u('/')

    @app.all
    def foo(this: str, req: Request, res: Response):
        await res.push("Hello world.")

    app.run()

----------

加点特技

    from isperdal import painting

    # callback
    '/'.all(
        lambda this, req, res:
            (await res.push("Hello world."))
    ).run()


    # decorator
    app = '/'

    @app.all
    def foo(this: str, req: Request, res: Response):
        await res.push("Hello world.")

    app.run()

Middleware
----------

基于分级的中间件

    '/'.all(lambda this, req, res: print("logger {} {}".format(req.method, req.uri)))
        .get('index')(lambda this, req, res: (await res.push("INDEX")))
        .get('app/'.all(
            lambda this, req, res: ('id' in req.session or (await res.redirect('/index')))
        ))(lambda this, req, res: (await res.push("/APP/")))
        .run()

----------

    app = '/'

    @app.all
    def logger(this, req, res):
        print("logger {} {}".format(req.method, req.uri))

    @app.get('index')
    def index(this, req, res):
        await res.push("INDEX")

    @app.get('app/'.all(
        lambda this, req, res: ('id' in req.session or (await res.redirect('/index')))
    ))
    def appindex(this, req, res):
        await res.push("/APP/")

    app.run()

Status
------

**TODO**


But..
=====

看起来很美好？
实际上只是个设想，说不定哪天 Rust 的官方`async IO`出来了就改用 Rust 了。
