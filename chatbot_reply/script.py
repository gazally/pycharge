#! /usr/bin/env python
# Copyright (c) 2016 Gemini Lasswell
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
""" chatbot_reply.script, defines decorators and superclass for chatbot scripts 
"""
from functools import wraps
import inspect
import random

from .exceptions import *

def rule(pattern_text, previous="", weight=1):
    def rule_decorator(func):
        @wraps(func)
        def func_wrapper(self, pattern=pattern_text, previous=previous,
                         weight=weight):
            result = func(self)
            try:
                return self.choose(result)
            except Exception, e:
                name = func.__module__ + "." + func.__name__
                e.args += (u" in Script.choose processing return value "
                           u"from {0}".format(name),)
        return func_wrapper
    return rule_decorator

def substitutions(subs, person=False):
    def substitutions_decorator(func):
        @wraps(func)
        def func_wrapper(self, name=subs, person=person):
            return func(self)
        return func_wrapper
    return substitutions_decorator

class ScriptRegistrar(type):
    registry = []
    def __new__(cls, name, bases, attributes):
        new_cls = type.__new__(cls, name, bases, attributes)
        if new_cls.__module__ != cls.__module__:
            cls.registry.append(new_cls)
        return new_cls

    @classmethod
    def clear(cls):
        cls.registry = []

class Script(object):
    __metaclass__ = ScriptRegistrar
    
    topic = "all"
    botvars = None
    uservars = None
    user_id = None
    match = None
    current_topic = None

    @classmethod
    def set_user(cls, user, uservars):
        cls.uservars = uservars
        cls.user_id = user
        cls.current_topic = uservars["__topic__"]
    
    @classmethod
    def set_topic(cls, new_topic):
        cls.current_topic = new_topic
        pass
    
    @staticmethod
    def choose(args):
        # self.choose can be a flexible thing, variable number of arguments
        # and they can be either strings or (string, weight) tuples
        # or just return either a string or a list to be fed to self.choose
        if args is None or not args:
            reply = ""
        else:
            reply = args
        if isinstance(args, list) and args:
            reply = random.choice(args)
            if isinstance(args[0], tuple):
                args = [(string, max(1, weight)) for string, weight in args]
                total = sum([weight for string, weight in args])
                choice = random.randrange(total)
                for string, weight in args:
                    if choice < abs(weight):
                        reply = string
                        break
                    else:
                        choice -= abs(weight)
        reply = reply.format(*[], **Script.match)
        return reply


def get_method_spec(name, method):
    """ Check that the passed argument spec matches what we expect the
    @rule decorator in scripts.py to do. Raises RuleMethodSpecError
    if a problem is found. If all is good, return the argspec
    (see inspect.getargspec)
    """
    if not hasattr(method, '__call__'):
        raise RuleMethodSpecError(
            u"{0} begins with 'rule' but is not callable.".format(
                name))
    argspec = inspect.getargspec(method)
    if (len(argspec.args) != 4 or
        " ".join(argspec.args) != "self pattern previous weight" or
        argspec.varargs is not None or
        argspec.keywords is not None or
        len(argspec.defaults) != 3):
        raise RuleMethodSpecError(u"{0} was not decorated by @rule "
                 "or it has the wrong number of arguments.".format(name))
    return argspec


