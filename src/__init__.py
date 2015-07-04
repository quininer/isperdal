#!/usr/bin/env python
# encoding: utf-8

from main import Microwave
from result import Result, Ok, Err

def only(handle):
    def only_wrap(this, req, res):
        if not req.subnode:
            return handle(this, req, res)
    return only_wrap
