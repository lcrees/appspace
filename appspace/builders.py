# -*- coding: utf-8 -*-
'''build appspaces'''

from __future__ import absolute_import

from operator import getitem, contains

from stuf.utils import selfname

from .utils import lru_cache
from .managers import Manager, appifies
from .error import AppLookupError, NoAppError
from .keys import AAppspace, ABranch, ANamespace


def include(module):
    '''
    configure branch appspace

    @param module: module import path
    '''
    return ('include', module)


@appifies(AAppspace)
class Appspace(object):

    '''appspace interface'''

    __slots__ = ['manager']

    def __init__(self, manager):
        '''
        init

        @param manager: appspace manager
        '''
        self.manager = manager

    def __getattr__(self, label):
        try:
            return object.__getattribute__(self, label)
        except AttributeError:
            return self.__getitem__(label)

    @lru_cache()
    def __getitem__(self, label):
        try:
            return self.manager.get(label)
        except AppLookupError:
            raise NoAppError('%s' % label)

    def __call__(self, label, *args, **kw):
        result = getitem(self, label)
        try:
            return result(*args, **kw)
        except TypeError:
            return result

    def __contains__(self, label):
        return contains(self.manager, label)

    def __repr__(self):
        return repr(self.manager)


class Factory(object):

    '''factory for appspace'''

    def __init__(self, label, manager, *args, **kw):
        '''
        init

        @param label: label for manager
        '''
        # object with manager configuration
        self._module = kw.get('module', 'appconf')
        # build manager
        self.manager = manager(self._module)
        # register apps in manager
        apper = self.manager.set
        # add applications
        [apper(*arg) for arg in args]  # pylint: disable-msg=W0106
        # add manager
        apper(label, Appspace(self.manager))

    def __repr__(self):
        return repr(self.manager)

    def build(self):
        '''build manager'''
        return Appspace(self.manager)


class Patterns(object):

    '''patterns for manager configured by class'''

    _manager = Manager

    def __repr__(self):
        return str(self._gather())

    @classmethod
    def _gather(cls):
        this = list()
        tappend = this.append
        textend = this.extend
        # filters
        anamespace = ANamespace.implementedBy
        branch = ABranch.implementedBy
        for k, v in vars(cls).iteritems():
            # filter private and hidden
            if not k.startswith('_'):
                # handle namespace
                if anamespace(v):
                    textend(i for i in v.build())
                # handle branches
                elif branch(v):
                    textend(v.build())
                # handle anything else
                else:
                    tappend((k, v))
        return this

    @classmethod
    def build(cls):
        '''build manager configuration from class'''
        this = list()
        tappend = this.append
        textend = this.extend
        # filters
        anamespace = ANamespace.implementedBy
        branch = ABranch.implementedBy
        for k, v in vars(cls).iteritems():
            # filter private and hidden
            if not k.startswith('_'):
                # handle namespace
                if anamespace(v):
                    textend(i for i in v.build())
                # handle branches
                elif branch(v):
                    textend(v.build())
                # handle anything else
                else:
                    tappend((k, v))
        # build configuration
        return cls.patterns(selfname(cls), *tuple(cls._gather()))

    @classmethod
    def patterns(cls, label, *args, **kw):
        '''
        configure appspace

        @param label: name of branch appspace
        @param *args: tuple of module paths or component inclusions
        '''
        return Factory(label, cls._manager, *args, **kw).build()


patterns = Patterns.patterns


@appifies(ABranch)
class Branch(object):

    '''branch configuration'''

    @classmethod
    def build(cls):
        '''gather branch configuration'''
        return [
            (k, include(v)) for k, v in vars(cls).iteritems()
            if all([not k.startswith('_'), isinstance(v, basestring)])
        ]


@appifies(ANamespace)
class Namespace(object):

    '''configuration namespace'''

    @classmethod
    def _pack(cls, this, that):
        '''build name'''
        return ('.'.join([selfname(cls), this]), that)

    @classmethod
    def build(cls):
        '''gather namespace configuration'''
        this = list()
        tappend = this.append
        textend = this.extend
        # filters
        anamespace = ANamespace.implementedBy
        pack = cls._pack
        for k, v in vars(cls).iteritems():
            if not k.startswith('_'):
                # handle namespaces
                if anamespace(v):
                    textend(pack(*i) for i in v.build())
                else:
                    tappend(pack(k, v))
        return this


__all__ = ('Branch', 'Namespace', 'Patterns', 'include', 'patterns')
