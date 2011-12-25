# -*- coding: utf-8 -*-
'''traits'''

from __future__ import absolute_import

from inspect import isclass, getmro
from functools import partial, update_wrapper

from stuf.utils import selfname, getter, setter

from .properties.core import TraitType
from .collections import ResetMixin, Sync
from .utils import get_appspace, component, get_component


def delegater(appspace):
    '''
    add appspace to class

    @param appspace: appspace to add
    '''
    Delegated.a = appspace
    Delegated.s = appspace.appspace.settings
    return Delegated


def delegatable(**kw):
    '''
    marks method as being able to be delegated

    @param **fkw: attributes to set on decorated method
    '''
    def wrapped(func):
        return Delegatable(func, **kw)
    return wrapped


def on(*events):
    '''
    marks method as being a lazy component

    @param label: component label
    @param branch: component branch (default: None)
    '''
    def wrapped(func):
        return On(func, *events)
    return wrapped


class On(object):

    '''attach events to method'''

    def __init__(self, method, *events):
        '''
        init

        @param method: method to tie to events
        @param *args: events
        '''
        self.events = events
        self.is_set = False
        self.method = method
        update_wrapper(self, method)

    def __get__(self, this, that):
        if not self.is_set:
            ebind = get_appspace(this, that).events.bind
            method = self.method
            for arg in self.events:
                ebind(arg, method)
            self.is_set = True
        return self.method


class Delegated(ResetMixin):

    '''attributes and methods can be delegated to appspaced components'''

    _descriptor_class = component
    _delegates = {}
    a = None
    s = None

    def _instance_component(self, name, label, branch=None):
        '''
        inject appspaced component as instance attribute

        @param name: instance attribute label
        @param label: component label
        @param branch: component branch (default: None)
        '''
        return setter(
            self,
            name,
            get_component(get_appspace(self, self.__class__), label, branch),
        )


class Delegatable(object):

    delegated = True

    def __init__(self, method, **kw):
        self.method = method
        self.kw = kw
        self.name = selfname(method)
        update_wrapper(self, method)

    def __get__(self, this, that):
        method = self.method
        delegates = that._delegates
        if delegates:
            kw = dict(
                (k, getter(that, v)) for k, v in delegates.iteritems()
                if hasattr(that, k)
            )
            if kw:
                method = partial(method, **kw)
        return setter(that, self.name, method)


class Meta(object):

    def __new__(cls, **kw):
        for k, v in kw.iteritems():
            setattr(cls, k, v)
        return super(Meta, cls).__new__(cls)

    def __repr__(self):
        return 'Meta: %s' % str(dict((k, v) for k, v in vars(
            self.__class__
        ).iteritems() if not k.startswith('_')))


class SynchedMixin(Delegated):

    def __init__(self, original, **kw):
        '''
        set trait values using keyword arguments

        We need to use setattr for this to trigger validation and events.
        '''
        super(SynchedMixin, self).__init__()
        self._sync = Sync(original, **kw)

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return unicode(dict(i for i in self._sync.public.iteritems()))


class MetaHasTraits(type):

    '''
    metaclass for HasTraits.

    This metaclass makes sure that any TraitType class attributes are
    instantiated and sets their name attribute.
    '''

    def __new__(cls, name, bases, classdict):
        '''
        instantiate all TraitTypes in class dict, setting their `name`
        attribute
        '''
        for k, v in classdict.iteritems():
            if TraitType.instance(v):
                v.name = k
            elif isclass(v):
                if TraitType.subclass(v):
                    vinst = v()
                    vinst.name = k
                    classdict[k] = vinst
        return super(MetaHasTraits, cls).__new__(cls, name, bases, classdict)

    def __init__(cls, name, bases, classdict):
        '''
        finish initializing HasTraits class.

        This sets the :attr:`this_class` attribute of each TraitType in the
        class dict to the newly created class ``cls``.
        '''
        for v in classdict.itervalues():
            if TraitType.instance(v):
                v.this_class = cls
        super(MetaHasTraits, cls).__init__(name, bases, classdict)


class HasTraitsMixin(SynchedMixin):

    __metaclass__ = MetaHasTraits
    _descriptor_class = TraitType
    c = None

    def __new__(cls, *args, **kw):
        # This is needed because in Python 2.6 object.__new__ only accepts the
        # cls argument.
        # pylint: disable-msg=e1101
        cls._metas = [b.Meta for b in getmro(cls) if hasattr(b, 'Meta')]
        # pylint: enable-msg=e1101
        new_meth = super(HasTraitsMixin, cls).__new__
        if new_meth is object.__new__:
            inst = new_meth(cls)
        else:
            inst = new_meth(cls, *args, **kw)
        inst._trait_dyn_inits = {}
        inst._trait_values = {}
        # set all TraitType instances to their default values
        for key in dir(cls):
            # Some descriptors raise AttributeError (like zope.interface's
            # __provides__ attributes even when they exist). This raises
            # AttributeErrors even though they are listed in dir(cls).
            try:
                value = getattr(cls, key)
            except AttributeError:
                pass
            else:
                if TraitType.instance(value):
                    value.instance_init(inst)
        return inst
