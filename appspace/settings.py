# -*- coding: utf-8 -*-
# pylint: disable-msg=f0401
'''settings'''

from __future__ import absolute_import

from stuf import frozenstuf, stuf
from stuf.utils import deepget, lazy_set, lazy, setter

from zope.interface import implements as appifies

from .utils import ResetMixin, object_walk
from .keys import ASettings, ADefaultSettings, ARequiredSettings


class AppspaceSettings(ResetMixin):

    '''appspace settings'''

    appifies(ASettings)

    def __init__(self, **kw):
        super(AppspaceSettings, self).__init__()
        self._final = stuf(**kw)
        self._default = stuf()
        self._required = stuf()

    @lazy_set
    def default(self):
        '''get default settings separately'''
        return frozenstuf(self._default)

    @default.setter
    def default(self, value):
        '''
        set default settings separately

        @param value: default settings
        '''
        if ADefaultSettings.implementedBy(value):
            self._default.clear()
            self.update_default(value)
        else:
            raise TypeError('invalid DefaultSettings')

    @lazy_set
    def required(self):
        '''get required settings separately'''
        return frozenstuf(self._default)

    @required.setter
    def required(self, value):
        '''
        set required settings separately

        @param value: required settings
        '''
        if ARequiredSettings.implementedBy(value):
            self._required.clear()
            self.update_required(value)
        else:
            raise TypeError('invalid RequiredSettings')

    @lazy
    def final(self):
        '''get final settings separately'''
        final = self._default.copy()
        final.update(self._final.copy())
        final.update(self._required.copy())
        return frozenstuf(final)

    def get(self, key, default=None):
        '''
        get value from settings

        @param key: key in settings
        @param default: default value
        '''
        default = deepget(self._default, key, default)
        return deepget(key, self._final, default)

    def set(self, key, value):
        '''
        set required settings separately

        @param key: key in settings
        @param value: value to put in settings
        '''
        try:
            path, key = key.rsplit('.', 1)
            try:
                setter(deepget(self._final, key), value)
            except AttributeError:
                paths = path.spit('.')
                this = self._final
                for part in paths:
                    new = stuf()
                    this[part] = new
                    this = new
                this[key] = value
        except ValueError:
            self._final[key] = value

    def update_default(self, settings):
        if ADefaultSettings.implementedBy(settings):
            self.reset()
            self._default.update(object_walk(settings))
        else:
            raise TypeError('invalid DefaultSettings')

    def update_required(self, settings):
        if ARequiredSettings.implementedBy(settings):
            self.reset()
            self._required.update(object_walk(settings))
        else:
            raise TypeError('invalid RequiredSettings')

    def update(self, *args, **kw):
        self._final.update(*args, **kw)


class DefaultSettings(object):

    '''default settings class'''

    appifies(ADefaultSettings)


class RequiredSettings(object):

    '''required settings class'''

    appifies(ARequiredSettings)