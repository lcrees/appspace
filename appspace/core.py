'''appspace builder'''

from appspace.error import NoAppError, AppLookupError
from appspace.util import name_resolver, checkname, reify, lru_cache
from appspace.state import (
    AAppSpace, AApp, AppSpace, global_appspace, ADefaultAppKey)

def appconf(appspace, *args, **kw):
    return App(AppFactory(appspace, *args, **kw).appspace)

def include(path):
    return ('include', path)

def patterns(appspace, *args, **kw):
    return AppFactory(appspace, *args, **kw)


class AppBase(object):

    @reify
    def _g(self):
        return self._appspace.getapp

    @reify
    def _q(self):
        return self._appspace.askapp


class AppFactory(AppBase):

    def __init__(self, name, *args, **kw):
        self._appconf = kw.get('appconf', 'apps')
        self._appname = kw.get('appname', 'apps')
        self._defapp = kw.get('app', AApp)
        self._global = kw.get('use_global', False)
        if isinstance(name, tuple) and name:
            self._name = self._checkname(name[0])
            nombus = name[1:]
            if nombus:
                newaf = AppFactory(nombus, *args, **kw).appspace
            else:
                newaf = AppFactory(self._name, *args, **kw).appspace
            self._s(newaf, AAppSpace, self._name)
        elif isinstance(name, basestring):
            self._name = name
            self._s(self._defapp, ADefaultAppKey)
            self._s(self._appspace, self._defapp, name)
            apper = self._app
            for arg in args: apper(*arg)

    @reify
    def _checkname(self):
        return checkname

    @reify
    def _dotted(self):
        return name_resolver.resolve

    @reify
    def _s(self):
        return self._appspace.setapp

    @reify
    def appspace(self):
        if self._global: return global_appspace
        return AppSpace(self._name)

    @reify
    def _appspace(self):
        return self.appspace

    def _app(self, name, path):
        if isinstance(path, basestring):
            self._g(AAppSpace, self._name).setapp(
                self._dotted(path), self._defapp, name,
            )
        elif isinstance(path, tuple):
            self._s(
                getattr(
                    self._dotted('.'.join([path[-1], self._appname])),
                    self._appconf,
                ).appspace,
                AAppSpace,
                name,
                app.__doc__,
            )


class App(AppBase):

    def __init__(self, appspace):
        self._appspace = appspace

    def __call__(self, name, *args, **kw):
        if not isinstance(name, tuple):
            return self._sort(self._resolve(name), *args, **kw)
        obj = self
        for n in name:
            obj = obj._resolve(n)
            if not isinstance(obj, App): return self._sort(obj, *args, **kw)

    def __contains__(self, name):
        try:
            self._g(self._defapp, name)
            return True
        except AppLookupError:
            return False

    def __getitem__(self, name):
        try:
            return self._resolve(name)
        except NoAppError:
            raise NoAppError('%s' % name)

    def __getattr__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return self._resolve(name)

    @reify
    def _defapp(self):
        return self._g(ADefaultAppKey)

    def _getspace(self, name=None):
        return self._q(AAppSpace, name, self._appspace)

    @lru_cache()
    def _resolve(self, name):
        try:
            return self._g(self._defapp, name)
        except AppLookupError:
            return App(self._getspace(name))

    @lru_cache(50)
    def _sort(self, result, *args, **kw):
        try:
            return result(*args, **kw)
        except TypeError:
            return result


# Global app shortcut
app = App(global_appspace)