# -*- coding: utf-8 -*-
'''appspace settings'''

from __future__ import absolute_import

import re
try:
    from types import ClassType, InstanceType
    classtypes = type, ClassType
except ImportError:
    classtypes = type
    InstanceType = None


def generic(func):
    '''
    create a simple generic function

    @param func: function to genericize

    This is a variation on version 0.8 of Philip J. Eby's simplegeneric module
    (http://pypi.python.org/pypi/simplegeneric).
    '''
    _sentinel = object()

    def _by_class(*args, **kw):
        cls = args[0].__class__
        for t in type(cls.__name__, (cls, object), {}).__mro__:
            f = _getbytype(t, _sentinel)
            if f is not _sentinel:
                return f(*args, **kw)
        else:
            return func(*args, **kw)

    _by_type = {object: func, InstanceType: _by_class}
    _getbytype = _by_type.get

    def when_type(*types):
        '''decorator to add a method that will be called for the given types'''
        for t in types:
            if not isinstance(t, classtypes):
                raise TypeError('%r is not a type or class' % t)

        def decorate(f):
            for t in types:
                if _by_type.setdefault(t, f) is not f:
                    raise TypeError(
                        '%r already has method for type %r' % (func, t)
                    )
            return f
        return decorate

    _by_object = {}
    _getbyobject = _by_object.get

    def when_object(*obs):
        '''decorator to add a method to be called for the given object(s)'''
        def decorate(f):
            for o in obs:
                if _by_object.setdefault(id(o), (o, f))[1] is not f:
                    raise TypeError(
                        '%r already has method for object %r' % (func, o)
                    )
            return f
        return decorate

    def dispatch(*args, **kw):
        f = _getbyobject(id(args[0]), _sentinel)
        if f is _sentinel:
            for t in type(args[0]).__mro__:
                f = _getbytype(t, _sentinel)
                if f is not _sentinel:
                    return f(*args, **kw)
            else:
                return func(*args, **kw)
        return f[1](*args, **kw)

    dispatch.__name__ = func.__name__
    dispatch.__dict__ = func.__dict__.copy()
    dispatch.__doc__ = func.__doc__
    dispatch.__module__ = func.__module__
    dispatch.when_type = when_type
    dispatch.when_object = when_object
    dispatch.default = func
    dispatch.has_object = lambda o: id(o) in _by_object
    dispatch.has_type = lambda t: t in _by_type
    return dispatch


def sort_nicely(iterable):
    '''
    Sort the given iterable in the way that humans expect.
    
    @param iterable: iterable to sort
    '''
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(iterable, key=alphanum_key)

__all__ = ['generic', 'sort_nicely']