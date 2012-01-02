# -*- coding: utf-8 -*-
'''appspace classes'''

from __future__ import absolute_import

from itertools import ifilter
from functools import partial, update_wrapper

from stuf.core import stuf
from stuf.utils import getter, selfname, setter, get_or_default

from appspace.core import appifies


from .query import __
from .core import AServer
from .utils import itermembers, keyed

__all__ = ['service', 'on', 'forward', 'local']


def service(*metadata):
    '''
    marks method as service

    @param *metadata: metadata to set on decorated method
    '''
    def wrapped(func):
        return Service(func, *metadata)
    return wrapped


def on(*events):
    '''
    marks method as being a lazy instance

    @param *events: list of properties
    '''
    def wrapped(func):
        return On(func, *events)
    return wrapped


class local(object):

    def __init__(self, label, branch=False, *args, **kw):
        self.label = label
        self.branch = branch
        self.attrs = args
        self.extra = kw

    def __get__(self, this, that):
        attrs = [getter(this, attr) for attr in self.attrs]
        new_app = __(that).app(self.label, self.branch)
        try:
            return new_app(*attrs, **self.extra)
        except TypeError:
            return new_app

    def __set__(self, this, value):
        raise AttributeError('attribute is read-only')

    def __delete__(self, this):
        raise AttributeError('attribute is read-only')


class forward(local):

    appifies(AServer)

    def __get__(self, this, that):
        delegates = get_or_default(that, 'D', stuf())
        this = stuf(ifilter(
            lambda x: keyed(AServer, x), itermembers(this),
        ))
        delegates.update(this)
        return local.__get__(self, this, that)


class Methodology(object):

    def __init__(self, method, *metadata):
        self.method = method
        self.metadata = metadata
        update_wrapper(self, method)


class Service(Methodology):

    '''method that can be delegated to another class'''

    def __get__(self, this, that):
        method = self.method
        if self.metadata:
            kw = dict(
                (k, getter(that, k)) for k in self.metadata if hasattr(this, k)
            )
            if kw:
                method = update_wrapper(partial(method, **kw), method)
        return method


class On(Methodology):

    '''attach events to method'''

    def __get__(self, this, that):
        ebind = __(that).manager.events.bind
        method = self.method
        for arg in self.events:
            ebind(arg, method)
        return setter(that, selfname(method), method)
