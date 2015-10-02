Example
-------

	from isperdal import Microwave as u

	# callback
	u('/').all()(
	    lambda this, req, res:
	        res.push("Hello world.").ok()
	).run()


	# decorator
	app = u('/')

	@app.all()
	def foo(this, req, res):
	    return res.push("Hello world.").ok()

	app.run()


Route
-----

以`/`分级。

认为`Route`应该是一棵树，`URL`是路径，
对`空中楼阁`式的`Route`不友好。

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

-----

	@app.append(u('posts/'), u(':pid/'), u('comment/'), u(':cid'), methods=('GET',))
	def postcomment(this, req, res):
	    pass

* 完全不推荐使用无状态的REST
* 完全不打算支持正则URL

返回响应
--------

节点间进行有序迭代，当函数返回`Ok`或`Err`实例时，跳出节点迭代。

* 参考自 `Rust` ??

多路由绑定
----------

多参数

	@app.route(u('/'), u('index'), methods=('get', 'post'))
	def index(this, req, res):
	    pass

Status WebSocket
----------------

连接即对象的状态友好模式。

	@app.get(u('websocket'))
	class websocket(WebSocket):
	    @coroutine
	    def on_connect(self):
	        if 'id' not in self.req.session:
	            raise res.err(403)
	        self.transport.send("You are successfully connected")

	    @coroutine
	    def on_message(self, message):
	        self.transport.send(message)

	    @coroutine
	    def on_close(self, exc=None):
	        print("Connection closed")

* 参考自 `Vase`

plugins
-------

中间件形式的插件

	from isperdal import Microwave as u
	from isperdal.middleware import logger, cookie, session, csrftoken

	app = u('/')

	app.all()(logger).all()(cookie).all()(session)

	@app.post(u('post').all()(csrftoken))
	def post(this, req, res):
	    pass

	app.run()

* 参考自 `expressjs`
