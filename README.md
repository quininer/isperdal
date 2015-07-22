isperdal
========

[![Build Status](https://travis-ci.org/quininer/isperdal.svg)](https://travis-ci.org/quininer/isperdal)

a web framework.

example:

    from isperdal import Microwave as u

    u('/').all()(
        lambda this, req, res:
            res.push("Hello world.")
    ).run()

reference
---------

* [Vase](https://github.com/vkryachko/Vase)
* [bottle](https://github.com/bottlepy/bottle)
* [expressjs](https://github.com/strongloop/express)
