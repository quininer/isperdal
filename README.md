isperdal
========

a web framework.

* 基于节点的路由分发
* 良好的中间件支持
* 状态友好的接口
* 可扩展的插件支持

example:

    from isperdal import painting

    '/'.all(
        lambda this, req, res:
            res.ok("Hello world.")
    ).run()
