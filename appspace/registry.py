# -*- coding: utf-8 -*-
'''appspace registries'''

import uuid
import hashlib
from inspect import isclass

from stuf.six import u
from appspace.keys import (
    AppStore, InterfaceClass, AApp, StrictAppStore, ANamespace, AManager)

__all__ = ('Registry', 'StrictRegistry')


class RegistryMixin(object):

    def __init__(self, label, key=AApp):
        '''
        init

        @param label: label for internal namespace
        @param key: registry key (default: AApp)
        '''
        super(RegistryMixin, self).__init__()
        self._key = key
        # root and current label
        self._root = self._current = label
        # register key under namespace
        self.ez_register(ANamespace, label, key)
        # register manager under label
        self.ez_register(AManager, label, self)

    @classmethod
    def create(cls):
        '''create new key'''
        return InterfaceClass(cls.uuid())

    @staticmethod
    def ez_id(this):
        '''
        easy unique identifier for an object

        @param this: an object
        '''
        return hashlib.sha1(u(id(this))).digest()

    def ez_lookup(self, key, label):
        '''
        streamlined app lookup

        @param key: key to lookup
        @param label: label to lookup
        '''
        return self.lookup1(key, key, label)

    def ez_register(self, key=None, label=None, app=None):
        '''
        streamlined app registration

        @param key: key to register
        @param label: label to register
        @param app: app to register
        '''
        self.register([key], key, label, app)

    def ez_subscribe(self, key, label, app):
        '''
        streamlined app subscription

        @param key: key to extend to
        @param label: label to extend to
        '''
        self.subscribe(key, self.key(key, label), app)

    def ez_unregister(self, key, label):
        '''
        streamlined app unregistration

        @param key: key to lookup
        @param label: label to lookup
        '''
        self.unregister([key], key, label, self.ez_lookup(key, label))

    unkey = ez_unregister

    def ez_unsubscribe(self, key, label):
        '''
        streamlined app unsubscription

        @param key: key to lookup
        @param label: label to lookup
        '''
        self.unsubscribe(key, self.ez_lookup(key, label))

    @staticmethod
    def keyed(k=False, v=False):
        '''
        check if item has an app key

        @param key: app key
        @param thing: thing to check
        '''
        try:
            return k.implementedBy(v) if isclass(v) else k.providedBy(v)
        except AttributeError:
            return False

    def key(self, key, label):
        '''
        create or fetch key

        @param key: key to register
        @param label: label to register
        '''
        this = self.lookup1(key, key, label)
        if this is None:
            this = self.create()
            self.register([key], key, label, this)
        return this

    @staticmethod
    def uuid():
        '''universal unique identifier'''
        return uuid.uuid4().hex.upper()


class Registry(RegistryMixin, AppStore):

    '''easy registry'''


class StrictRegistry(RegistryMixin, StrictAppStore):

    '''strict registry'''
