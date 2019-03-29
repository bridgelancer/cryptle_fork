"""
Copyright (C) 2018 Interactive Brokers LLC. All rights reserved. This code is subject to the terms
and conditions of the IB API Non-Commercial License or the IB API Commercial License, as applicable.
"""


"""
Collection of misc tools
"""


import sys
import logging
import inspect
from typing import Tuple, Dict, Any

from .common import UNSET_INTEGER, UNSET_DOUBLE, get_logger


logger = get_logger()


# I use this just to visually emphasize it's a wrapper overriden method
def iswrapper(fn):
    return fn


class BadMessage(Exception):
    def __init__(self, text):
        self.text = text


def parent_fn_context() -> Tuple[str, Dict[str, Any]]:
    # depth is 2 bc this is already a fn, whereas we need the parent of the caller
    try:
        frameinfo = inspect.getouterframes(inspect.currentframe())[2]
    except IndexError:
        raise IndexError("No parent frame")
    else:
        return frameinfo.function, frameinfo.frame.f_locals


def current_fn_name(parent_idx=0):
    # depth is 1 bc this is already a fn, so we need the caller
    return sys._getframe(1 + parent_idx).f_code.co_name


def setattr_log(self, var_name, var_value):
    # import code; code.interact(local=locals())
    logger.debug("%s %s %s=|%s|", self.__class__, id(self), var_name, var_value)
    super(self.__class__, self).__setattr__(var_name, var_value)


SHOW_UNSET = True


def decode(the_type, fields, show_unset=False):
    try:
        s = next(fields)
    except StopIteration:
        raise BadMessage("no more fields")

    logger.debug("decode %s %s", the_type, s)

    if the_type is str:
        if type(s) is str:
            return s
        elif type(s) is bytes:
            return s.decode()
        else:
            raise TypeError(
                "unsupported incoming type " + type(s) + " for desired type 'str"
            )

    orig_type = the_type
    if the_type is bool:
        the_type = int

    if show_unset:
        if s is None or len(s) == 0:
            if the_type is float:
                n = UNSET_DOUBLE
            elif the_type is int:
                n = UNSET_INTEGER
            else:
                raise TypeError("unsupported desired type for empty value" + the_type)
        else:
            n = the_type(s)
    else:
        n = the_type(s or 0)

    if orig_type is bool:
        n = False if n == 0 else True

    return n


def ExerciseStaticMethods(klass):

    import types, inspect

    # import code; code.interact(local=dict(globals(), **locals()))
    for (name, var) in inspect.getmembers(klass):
        # print(name, var, type(var))
        if type(var) == types.FunctionType:
            print("Exercising: %s:" % var)
            print(var())
            print()
