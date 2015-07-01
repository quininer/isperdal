forbiddenfruit
--------------

Normal

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


Magic

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


Route
-----

以`/`分级。

认为URL应该是一棵树，
对`空中楼阁`式的URL不友好。

                 "/"
                 / \
                /   \
         "assets/"  "posts/"
            /  |       | \
           /   |       |  \
         img  css     (1  (2
                       X    \
                      / \    \
                     "comment/" ---> POST
                    /     \    \
                  (1      (2    (1

    GET     /posts/1
    POST    /posts/1/comment
    GET     /posts/1/comment/2

* 完全不推荐使用无状态的REST
* 完全不打算支持正则URL

返回响应?
---------

1. 判断每个节点函数返回值，若是`Ok`类的实例，则中断迭代返回`res`
    - 可以用树状路由
    - 不能使用防止在后面的中间件
2. 完成所有节点迭代，返回最终的`res`
    - 容易混淆末节点
    - 需要用列表路由

Middleware
----------

基于节点路由的中间件，
非 wsgi 中间件，
本质上不区分 Middleware 与 APP。

* [callback](/examples/app.callback.py#L9)
* [decorator](/examples/app.decorator.py#L17)

Status
------

pass

plugins
-------

pass
