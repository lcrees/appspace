# -*- coding: utf-8 -*-
'''appspace exceptions'''

from __future__ import absolute_import

from .core import AppLookupError

__all__ = [
    'AppLookupError', 'ConfigurationError', 'NoAppspaceError', 'NoAppError',
]

AppLookupError = AppLookupError


class ConfigurationError(Exception):

    '''appspace configuration exception'''


class NoAppspaceError(Exception):

    '''no appspace found error'''


class NoAppError(Exception):

    '''mo application found exception'''
