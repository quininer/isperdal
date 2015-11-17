isperdal
========

[![Build Status](https://travis-ci.org/quininer/isperdal.svg)](https://travis-ci.org/quininer/isperdal)

a Web framework, asyncio based.

example:

    from isperdal import Node as u

    u('/').all()(
        lambda this, req, res:
            res.push("Hello world.")
    ).run()

reference
---------

* [Vase](https://github.com/vkryachko/Vase)
* [bottle](https://github.com/bottlepy/bottle)
* [expressjs](https://github.com/strongloop/express)
