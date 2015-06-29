#!/usr/bin/env python
# encoding: utf-8

from isperdal import painting

'/'.all(
    lambda this, req, res:
        (await res.push("Hello world."))
).run()
