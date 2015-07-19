#!/usr/bin/env python
# encoding: utf-8

from .node import Microwave


def only(handle):
    def only_wrap(this, req, res):
        if not req.next:
            return handle(this, req, res)
    return only_wrap
