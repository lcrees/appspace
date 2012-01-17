# -*- coding: utf-8 -*-
'''extension services management'''

from __future__ import absolute_import

from functools import wraps

from appspace.query import direct, factory

from .query import S
from .keys import AService


class forward(factory):

    '''builds application in appspace and forwards host functionality to it'''


class remote(direct):

    '''makes remote functionality directly available to client'''


def service(*metadata):
    '''
    marks method as service

    @param *metadata: metadata to set on decorated method
    '''
    def wrapped(this):
        this.metadata = metadata
        S.key(AService, this)
        @wraps(this) #@IgnorePep8
        def wrapper(*args, **kw):
            return this(*args, **kw)
        return wrapper
    return wrapped


class servicer(factory):

    '''builds service and makes it available to clients'''


__all__ = ('servicer', 'forward', 'remote', 'service')
