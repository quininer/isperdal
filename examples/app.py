#!/usr/bin/env python
# encoding: utf-8

from isperdal import microwave

'/'.all(
    lambda this, req, res:
        (await res.push("Hello world."))
).run()
