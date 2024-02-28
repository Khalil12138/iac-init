# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import os
import importlib
import importlib.util
from iac_init.conf import global_settings
from iac_init.utils.functional import LazyObject, empty
from iac_init.utils.exceptions import ImproperlyConfigured

ENVIRONMENT_VARIABLE = "IAC_INIT_SETTINGS_MODULE"

class SettingsReference(str):
    """
    String subclass which references a current settings value. It's treated as
    the value in memory but serializes to a settings.NAME attribute reference.
    """

    def __new__(self, value, setting_name):
        return str.__new__(self, value)

    def __init__(self, value, setting_name):
        self.setting_name = setting_name

class LazySettings(LazyObject):
    def _setup(self, name=None):
        settings_module = os.environ.get(ENVIRONMENT_VARIABLE)
        if not settings_module:
            desc = ("setting %s" % name) if name else "settings"
            raise ImproperlyConfigured(
                "Requested %s, but settings are not configured. "
                "You must either define the environment variable %s "
                "or call settings.configure() before accessing settings."
                % (desc, ENVIRONMENT_VARIABLE)
            )

        self._wrapped = Settings(settings_module)

    def __repr__(self):
        # Hardcode the class name as otherwise it yields 'Settings'.
        if self._wrapped is empty:
            return "<LazySettings [Unevaluated]>"

        return '<LazySettings "%(settings_module)s">' % {
            "settings_module": self._wrapped.SETTINGS_MODULE,
        }

    def __getattr__(self, name):
        """Return the value of a setting and cache it in self.__dict__."""
        _wrapped = None
        if (_wrapped := self._wrapped) is empty:
            self._setup(name)
            _wrapped = self._wrapped
        val = getattr(self._wrapped, name)

        # Special case some settings which require further modification.
        # This is done here for performance reasons so the modified value is cached.

        self.__dict__[name] = val
        return val

    def __setattr__(self, name, value):
        """
        Set the value of setting. Clear all cached values if _wrapped changes
        (@override_settings does this) or clear single values when set.
        """
        if name == "_wrapped":
            self.__dict__.clear()
        else:
            self.__dict__.pop(name, None)
        super().__setattr__(name, value)

    def __delattr__(self, name):
        """Delete a setting and clear it from cache if needed."""
        super().__delattr__(name)
        self.__dict__.pop(name, None)

class Settings:
    def __init__(self, settings_module):
        # update this dict from global settings (but only for ALL_CAPS settings)
        for setting in dir(global_settings):
            if setting.isupper():
                setattr(self, setting, getattr(global_settings, setting))

        # store the settings module in case someone later cares
        self.SETTINGS_MODULE = settings_module

        spec = importlib.util.spec_from_file_location("mod", self.SETTINGS_MODULE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        dict_settings = (
            "APIC_DEVICES",
            "DEFAULT_USER_OPTIONS",
            "DEFAULT_DATA_PATH",
        )

        self._explicit_settings = set()
        for setting in dir(mod):
            if setting.isupper():
                setting_value = getattr(mod, setting)

                if setting in dict_settings and not isinstance(
                    setting_value, (list, dict)
                ):
                    raise ImproperlyConfigured(
                        "The %s setting must be a list or a dict." % setting
                    )
                setattr(self, setting, setting_value)
                self._explicit_settings.add(setting)

settings = LazySettings()
