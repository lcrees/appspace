# -*- coding: utf-8 -*-
'''service classes'''

from __future__ import absolute_import

from appspace.keys import appifies
from appspace.ext.classes import ResetMixin

from .keys import AClient, AServer
from .decorators import forward, remote


class client(type):

    '''capture server names'''

    def __init__(cls, name, bases, classdict):
        items = (forward, remote)
        cls._servers = set(
            k for k, v in classdict.iteritems() if isinstance(v, items)
        )
        super(client, cls).__init__(name, bases, classdict)


@appifies(AClient)
class Client(ResetMixin):

    '''consumes services from other instances'''

    __metaclass__ = client

    def __getattr__(self, key):
        try:
            return super(Client, self).__getattr__(key)
        except AttributeError:
            return self._S.resolve(key, self)


@appifies(AServer)
class Server(ResetMixin):

    '''provides services for other instances'''


__all__ = ('Client', 'Server')
