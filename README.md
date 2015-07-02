isperdal
========

a web framework.

* 基于节点的路由分发
* 良好的中间件支持
* 状态友好的`WebSocket`接口
* 可扩展的插件支持

example:

    from isperdal import painting

    '/'.all(
        lambda this, req, res:
            res.ok("Hello world.")
    ).run()

reference
---------

* [Vase](https://github.com/vkryachko/Vase)
* [bottle](https://github.com/bottlepy/bottle)
* [expressjs](https://github.com/strongloop/express)
