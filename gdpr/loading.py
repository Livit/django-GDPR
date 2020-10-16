# -*- coding: future_fstrings -*-
from __future__ import absolute_import

from collections import OrderedDict
from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.utils.encoding import force_text
from typing import Generic, Type, TypeVar

from .utils import str_to_class


class BaseLoader(object):
    u"""Base class for all loaders."""

    def import_modules(self):
        raise NotImplementedError


class AppLoader(BaseLoader):
    u"""Scan all installed apps for `module_name` module."""

    module_name = None

    def import_modules(self):
        for app in apps.get_app_configs():
            if app.name == u'gdpr':
                continue
            try:
                import_module(u'{}.{}'.format((app.name), (self.module_name)))
            except ImportError, ex:
                if force_text(ex) != u'No module named \'{}.{}\''.format((app.name), (self.module_name)):
                    raise ex


class SettingsListLoader(BaseLoader):
    u"""Import all modules from list `list_name` in settings."""

    list_name = None

    def import_modules(self):
        if not hasattr(settings, self.list_name):
            raise ImproperlyConfigured(u'settings.{} not found.'.format((self.list_name)))
        modules_list = getattr(settings, self.list_name)
        if type(modules_list) in [list, tuple]:
            for i in modules_list:
                import_module(i)
        else:
            raise ImproperlyConfigured(u'settings.{} have incorrect type {}.'.format((self.list_name), (unicode(type(modules_list)))))


class SettingsListAnonymizerLoader(SettingsListLoader):
    u"""Load all anonymizers from settings.GDPR_ANONYMIZERS_LIST list."""

    list_name = u'GDPR_ANONYMIZERS_LIST'


class SettingsListPurposesLoader(SettingsListLoader):
    u"""Load all purposes from settings.GDPR_PURPOSES_LIST list."""

    list_name = u'GDPR_PURPOSES_LIST'


class AppAnonymizerLoader(AppLoader):
    u"""Scan all installed apps for anonymizers module which should contain anonymizers."""

    module_name = u'anonymizers'


class AppPurposesLoader(AppLoader):
    u"""Scan all installed apps for purposes module which should contain purposes."""

    module_name = u'purposes'


K = TypeVar(u'K')
V = TypeVar(u'V')


class BaseRegister(Generic[K, V]):
    u"""Base class for all registers."""

    _is_import_done = False
    register_dict = None
    loaders_settings = None
    default_loader = None

    def __init__(self):
        self.register_dict = OrderedDict()

    def register(self, key, object_class):
        self.register_dict[key] = object_class

    def _import_objects(self):
        default_loader = [self.default_loader] if self.default_loader else []
        for loader_path in getattr(settings, self.loaders_settings, default_loader):
            if isinstance(loader_path, (list, tuple)):
                for path in loader_path:
                    import_module(path)
            else:
                str_to_class(loader_path)().import_modules()

    def _import_objects_once(self):
        if self._is_import_done:
            return
        self._is_import_done = True
        self._import_objects()

    def __iter__(self):
        self._import_objects_once()

        for o in self.register_dict.values():
            yield o

    def __contains__(self, key):
        self._import_objects_once()

        return key in self.register_dict.keys()

    def __getitem__(self, key):
        self._import_objects_once()

        return self.register_dict[key]

    def keys(self):
        self._import_objects_once()

        return self.register_dict.keys()

    def items(self):
        self._import_objects_once()

        return self.register_dict.items()

    def values(self):
        self._import_objects_once()

        return self.register_dict.values()

    def get(self, *args, **kwargs):
        self._import_objects_once()

        return self.register_dict.get(*args, **kwargs)


class AnonymizersRegister(BaseRegister[Model, Type[u"ModelAnonymizer"]]):
    u"""
    AnonymizersRegister is storage for found anonymizer classes.
    """

    default_loader = u'gdpr.loading.AppAnonymizerLoader'
    loaders_settings = u'ANONYMIZATION_LOADERS'


class PurposesRegister(BaseRegister[unicode, Type[u"AbstractPurpose"]]):
    u"""
    PurposesRegister is storage for found purpose classes.
    """

    default_loader = u'gdpr.loading.AppPurposesLoader'
    loaders_settings = u'PURPOSE_LOADERS'


anonymizer_register = AnonymizersRegister()
purpose_register = PurposesRegister()
