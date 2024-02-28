# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import os
import re
import logging
from typing import Any, Dict, List, Optional
from iac_init.scripts.ssh_tool import check_ssh_connection

logger = logging.getLogger(__name__)

class Validator:
    def __init__(self, data_path: str, settings_path: str):
        self.data: Optional[Dict[str, Any]] = None
        self.data_path = data_path
        self.settings_path = settings_path
        self.errors: List[str] = []

        self._wrapped = self._validate_path

    def _validate_path(self):
        '''Validate if user provided setting file exist and must be a python file'''
        if os.path.exists(self.settings_path) and os.path.isfile(self.settings_path):
            pass
        else:
            msg = "Tool Settings Config File not found: {}".format(self.settings_path)
            logger.error(msg)
            self.errors.append(msg)
            return True
        if self.settings_path.endswith(".py"):
            pass
        else:
            msg = "Settings Config File must be a python file (end with .py): {}".format(self.settings_path)
            logger.error(msg)
            self.errors.append(msg)
            return True

        '''Validate if user provided yaml directory exist'''
        if os.path.exists(self.data_path):
            if not os.path.isfile(self.data_path):
                pass
            else:
                msg = "Yaml Directory must be a directory not a file.: {}".format(self.data_path)
                logger.error(msg)
                self.errors.append(msg)
                return True
        else:
            msg = "Yaml Directory must be a directory not a file.: {}".format(self.data_path)
            logger.error(msg)
            self.errors.append(msg)
            return True

        logger.info("Loaded settings file: {} and Yaml directory: {}".format(self.settings_path, self.data_path))
        os.environ.setdefault('IAC_INIT_SETTINGS_MODULE', self.settings_path)

        return self._validate_ip()

    def _validate_ip(self):
        from iac_init.conf import settings
        if settings.APIC_DEVICES:
            msg = "Validate error '{}': Can not meet IP Address Format.\n".format(self.settings_path)
            for ip in settings.APIC_DEVICES:
                p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
                if not p.match(ip):
                    msg = msg + "{}".format(ip)
            if msg != "Validate error '{}': Can not meet IP Address Format.\n".format(self.settings_path):
                logger.error(msg)
                self.errors.append(msg)
                return True
        else:
            msg = "Validate error '{}': APIC_DEVICES is Null".format(self.settings_path)
            logger.error(msg)
            self.errors.append(msg)
            return True

        return self._validate_ssh_connection()

    def _validate_ssh_connection(self):
        from iac_init.conf import settings

        msg = "Validate error: APIC SSH Fail.\n"
        fail_dev_list = []

        for ip in settings.APIC_DEVICES:
            connection_state = check_ssh_connection(ip, settings.APIC_USERNAME, settings.APIC_PASSWORD)
            if not connection_state:
                fail_dev_list.append(ip)

        if fail_dev_list:
            msg += ",".join(fail_dev_list)
            logger.error(msg)
            self.errors.append(msg)
            return True

        logger.info("APIC SSH Connection Success.")
        return

    def _validate_choices(self, value):
        from iac_init.conf import settings
        choices = value.split(',')
        valid_choices = [str(i) for i in range(1, len(settings.DEFAULT_USER_OPTIONS)+1)]
        for choice in choices:
            if choice not in valid_choices:
                msg = '{} is not a valid choice'.format(choice)
                logger.error(msg)
                self.errors.append(msg)
                return
        self.choices = sorted(choices, key=lambda x: int(x))
        self.options = value
        return self.choices

    def _validate_bool(self, bool):
        if bool == "yes":
            pass
        else:
            exit(1)
