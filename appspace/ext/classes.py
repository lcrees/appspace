# -*- coding: utf-8 -*-
'''appspace extension classes'''

from __future__ import absolute_import

from stuf.utils import either, setter

from appspace.keys import appifies

from .apps import __
from .services import S
from .keys import AClient, AServer
from .containers import ResetMixin, Sync


class Host(ResetMixin):

    '''can have appspaced components attached'''


class Client(Host):

    '''consumes services from other instances'''

    appifies(AClient)

    def __init__(self):
        super(Client, self).__init__()
        # service tracker
        self._services = set()

    def __getattr__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            # check for services
            if any([not key.startswith('__'), not key.upper()]):
                return setter(self, key, S(self).fetch(key))


class Server(Host):

    '''hosts services for other instances'''

    appifies(AServer)


class Synched(Host):

    '''instance with synchronizing functionality'''

    def __init__(self, original, **kw):
        '''
        init

        @param original: data to synchronize
        '''
        super(Synched, self).__init__()
        self._sync = Sync(original, **kw)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return unicode(dict(i for i in self._sync.public.iteritems()))

    @either
    def C(self):
        '''local settings'''
        return __(self).localize().one()


__all__ = ('Client', 'Host', 'Server', 'Synched')
