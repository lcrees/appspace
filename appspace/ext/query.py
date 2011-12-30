# -*- coding: utf-8 -*-
'''manager query'''

from __future__ import absolute_import

from inspect import getmro
from collections import deque
from functools import partial, update_wrapper

from stuf import stuf
from stuf.utils import clsname, getter, get_or_default, selfname, setter

from appspace.core import AAppspace
from appspace.decorators import NoDefaultSpecified
from appspace.utils import getcls, itermembers, modname
from appspace.error import NoAppError, ConfigurationError
from appspace.builders import Appspace, Manager, Patterns, patterns


def delegatable(*metadata):
    '''
    marks method as delegatable

    @param *metadata: metadata to set on decorated method
    '''
    def wrapped(func):
        return Delegatable(func, *metadata)
    return wrapped


def lazy_component(branch=''):
    '''
    marks method as a lazily loaded component

    @param branch: component branch (default: '')
    '''
    def wrapped(func):
        return LazyComponent(func, branch)
    return wrapped


def on(*events):
    '''
    marks method as being a lazy component

    @param *events: list of properties
    '''
    def wrapped(func):
        return On(func, *events)
    return wrapped


class Query(deque):

    '''manager query'''

    def __init__(self, appspace, *args, **kw):
        '''
        @param manager: an manager
        '''
        try:
            self._appspace = appspace.A
            self._this = appspace
        except (AttributeError, NoAppError):
            if AAppspace.providedBy(appspace):
                self._appspace = appspace
                self._this = kw.pop('this', None)
            else:
                raise NoAppError('appspace not found')
        self.manager = self._appspace.manager
        self.settings = self._appspace.manager.settings
        deque.__init__(self, *args)

    def __call__(self, *args):
        return getcls(self)(self._appspace, *args, **dict(this=self._this))

    def _freshen(self, this):
        '''
        clear and put one thing in queue

        @param this: the thing
        '''
        # clear
        self.clear()
        # append to queue
        self.appendleft(this)
        return self

    def api(self, that):
        '''
        fetch api matching type of class

        @param that: class to filter by
        '''
        combined = []
        cextend = combined.extend
        for meths in self.filter(that):
            cextend(meths)
        if combined:
            branch = self(self.branch(self.key().one()))
            sappend = self.appendleft
            bapp = branch.app
            this = self._this
            for k, v in combined:
                new = v.__get__(None, this)
                bapp(k, new)
                sappend((k, new))
        return self

    def app(self, label, branch='', app=''):
        '''
        add or get application from appspace

        @param label: application label
        @param branch: branch label (default: '')
        @param app: new application (default: '')
        '''
        if app:
            if branch:
                manager = self.branch(branch).one().manager
            else:
                manager = self.manager
            manager.set(label, app)
            return self._freshen(app)
        if branch:
            return self._freshen(self._appspace[branch][label])
        return self._freshen(self._appspace[label])

    def apply(self, label, branch='', *args, **kw):
        '''
        call application from appspace

        @param label: application label
        @param branch: branch label (default: '')
        '''
        return self._freshen(self._appspace[branch][label](*args, **kw))

    @classmethod
    def appspace(cls, pattern, required=None, defaults=None, *args, **kw):
        '''
        build new appspace

        @param pattern: pattern configuration class or appspace label
        @param required: required settings
        @param defaults: default settings
        @param *args: tuple of module paths or component inclusions
        '''
        if issubclass(pattern, Patterns):
            return cls(pattern.build(required, defaults))
        elif isinstance(pattern, basestring) and args:
            return cls(Patterns.settings(
                patterns(pattern, *args, **kw), required, defaults,
            ))
        raise ConfigurationError('patterns not found')

    def branch(self, label):
        '''
        add or get branch appspace

        @param label: label of appspace
        '''
        try:
            return self._freshen(self._appspace[label])
        except NoAppError:
            new_appspace = Appspace(Manager())
            self.manager.set(label, new_appspace)
            return self._freshen(new_appspace)
        raise ConfigurationError('invalid branch configuration')

    def delegated(self):
        '''list delegated attributes'''
        self.clear()
        combined = []
        cextend = combined.extend
        for meths in self.filter('_delegatedable'):
            cextend(i for i in self(meths).delegatable())
        if combined:
            keys = set(k[0] for k in combined)
            self.settings.delegates[self.key().one()] = keys
            return self._freshen(keys)
        return self

    def delegatable(self):
        '''list delegatable attributes'''
        self.clear()
        return self.api('_delegatableable')

    def filter(self, that):
        '''
        filter object members by a class

        @param that: class to filter by
        '''
        test = lambda x: hasattr(x, that)
        self.extendleft(i for i in itermembers(self._this, test))
        return self

    def localize(self, **kw):
        '''
        generate local settings for component

        **kw: settings to add to local settings
        '''
        this = self._this
        metas = [b.Meta for b in getmro(getcls(this)) if hasattr(b, 'Meta')]
        meta = get_or_default(this, 'Meta')
        if meta:
            metas.append(meta)
        key = self.key().one()
        local_settings = self.settings.local[key] = stuf(
            dict((k, v) for k, v in vars(m).iteritems()
            if not k.startswith('_')) for m in metas
        )
        local_settings.update(kw)
        return self._freshen(local_settings)

    def key(self):
        '''identifier for component'''
        return self._freshen(
            '_'.join([modname(self._this), clsname(self._this)]).lower()
        )

    def one(self):
        '''fetch one result'''
        try:
            return self[0]
        except IndexError:
            return []

    def ons(self):
        '''list of events'''
        self.clear()
        return self.api('_onable')

    first = one

    def register(self, appspaced):
        '''
        add appspace to class

        @param appspaced: class to be appspaced
        '''
        # attach manager
        setter(appspaced, 'A', self._appspace)
        # attach manager settings
        setter(appspaced, 'S', self.settings)
        return self._freshen(appspaced)

    def setting(self, key, value=NoDefaultSpecified, default=None):
        '''
        change setting in application settings

        @param key: name of settings
        @param value: value in settings
        @param default: setting value (default: None)
        '''
        if not isinstance(value, NoDefaultSpecified):
            self.settings.set(key, value)
            return self
        return self._freshen(self.settings.get(key, default))


class component(object):

    '''attach appspaced component to class'''

    def __init__(self, label, branch=''):
        '''
        @param label: component label
        @param branch: component branch (default: '')
        '''
        self.label = label
        self.branch = branch
        self._appspace = False

    def __get__(self, this, that):
        return self.calculate(that)

    def __set__(self, this, value):
        raise AttributeError('attribute is read only')

    def __delete__(self, this):
        raise AttributeError('attribute is read only')

    def __repr__(self, *args, **kwargs):
        return '{label}@{branch}'.format(label=self.label, branch=self.branch)

    def calculate(self, that):
        return self.component(that)

    def component(self, that):
        '''
        get component from manager

        @param that: the instance's class
        '''
        return __(that).app(self.label, self.branch).one()


class delegated(component):

    '''delegated component'''

    _delegatedable = True


class LazyComponent(component):

    '''lazily load appspaced component'''

    def __init__(self, method, branch=''):
        '''
        @param label: component label
        @param branch: component branch (default: '')
        '''
        super(LazyComponent, self).__init__(selfname(method), branch)
        self.method = method
        update_wrapper(self, method)

    def compute(self, this, that):
        __(that).app(self.label, self.branch, self.method(this))
        return super(LazyComponent, self).compute(this, that)


class Delegatable(LazyComponent):

    '''manager component that can be delegated to another class'''

    _delegatableable = True

    def __init__(self, method, branch='', *metadata):
        super(Delegatable, self).__init__(method, branch)
        self.metadata = metadata

    def compute(self, this, that):
        method = self.method
        delegates = self.metadata
        if delegates:
            kw = dict(
                (k, getter(that, k)) for k in delegates if hasattr(that, k)
            )
            if kw:
                method = partial(method, **kw)
        return setter(that, self.label, method)


class On(LazyComponent):

    '''attach events to method'''

    _onable = True

    def __init__(self, method, branch='', *events):
        super(On, self).__init__(method, branch)
        self.events = events

    def compute(self, this, that):
        ebind = __(that).manager.events.bind
        method = self.method
        for arg in self.events:
            ebind(arg, method)
        return setter(that, self.label, self.method)


# shortcut
__ = Query