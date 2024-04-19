# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import os
import re
import shutil
import logging
from ruamel import yaml
from loguru import logger
from typing import Any, Dict, List, Optional

from iac_init.conf import settings
from iac_init.yaml_conf.yaml import load_yaml_files
from iac_init.scripts.ssh_tool import check_ssh_connection
from iac_init.scripts.apic_connecton_tool import apic_login
from iac_init.scripts.cimc_precheck_tool import cimc_precheck
from iac_init.scripts.telnet_tool import check_tennet_connection

logger.add(sink=os.path.join(settings.OUTPUT_BASE_DIR, 'iac_init_log', 'iac-init-main.log'), format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}', encoding='utf-8')

class Validator:
    def __init__(self, data_path: str, output: str):
        self.data: Optional[Dict[str, Any]] = None
        self.data_path = data_path
        self.output = output
        self.global_policy = None
        self.errors: List[str] = []

        self._wrapped = self._validate_path

    def _validate_path(self):
        '''Validate if user provided yaml directory exist'''
        if os.path.exists(self.data_path):
            if os.path.isdir(self.data_path):
                pass
            else:
                msg = "Yaml Directory must be a directory not a file.: {}".format(self.data_path)
                logger.error(msg)
                self.errors.append(msg)
                return True
        else:
            msg = "Yaml Directory not exist.: {}".format(self.data_path)
            logger.error(msg)
            self.errors.append(msg)
            return True

        logger.info("Loaded Yaml directory: {}".format(self.data_path))

        return self._validate_yaml()

    def _validate_syntax_file(self, file_path: str):
        """Run syntactic validation for a single file"""
        filename = os.path.basename(file_path)
        if os.path.isfile(file_path) and (".yaml" in filename or ".yml" in filename):
            logger.info("Validate file: {}".format(filename))

            # YAML syntax validation
            try:
                load_yaml_files([file_path])
            except yaml.error.MarkedYAMLError as e:
                line = 0
                column = 0
                if e.problem_mark is not None:
                    line = e.problem_mark.line + 1
                    column = e.problem_mark.column + 1
                msg = "Syntax error '{}': Line {}, Column {} - {}".format(
                    file_path,
                    line,
                    column,
                    e.problem,
                )
                logger.error(msg)
                self.errors.append(msg)

    def _validate_yaml(self):
        for dir, _, files in os.walk(self.data_path):
            for filename in files:
                self._validate_syntax_file(os.path.join(dir, filename))
                if settings.DEFAULT_DATA_PATH == filename:
                    self.global_policy = os.path.join(dir, filename)
        if self.global_policy:
            settings.global_policy = load_yaml_files([self.global_policy])
        else:
            msg = "Configuration File {} not fount".format(settings.DEFAULT_DATA_PATH)
            logger.error(msg)
            self.errors.append(msg)
            return True

        return self._load_connnection_info()

    def _load_connnection_info(self):
        try:
            self.aci_local_credential = [
                settings.global_policy['fabric']['global_policies']['aci_local_username'],
                settings.global_policy['fabric']['global_policies']['aci_local_password']
            ]

            self.apic_cimc_credential = [
                settings.global_policy['fabric']['global_policies']['apic_cimc_username'],
                settings.global_policy['fabric']['global_policies']['apic_cimc_password']
            ]

            self.apic_address = [
                data['apic_address'] for data in settings.global_policy['fabric']['apic_nodes_connection']
            ]

            self.cimc_address = [
                data['cimc_address'] for data in settings.global_policy['fabric']['apic_nodes_connection']
            ]

            self.switch_list = [
                [data['console_address'], data['console_port']] for data in settings.global_policy['fabric']['switch_nodes_connection']
            ]

            self.total_ip_list = self.apic_address + self.cimc_address + [data['console_address']
                                                                          for data in settings.global_policy['fabric']['switch_nodes_connection']]

            settings.cimc_list = self.cimc_address
            settings.apic_list = self.apic_address
            settings.aci_local_credential = self.aci_local_credential
            settings.apic_cimc_credential = self.apic_cimc_credential
            settings.switch_list = [':'.join(map(str, item)) for item in self.switch_list]

            return self._validate_ip()

        except Exception as e:
            msg = e
            logger.error(msg)
            self.errors.append(str(msg))
            return True

    def _validate_ip(self):
        if self.total_ip_list:
            msg = "Validate error :Below IP can not meet IP Address Format.\n"
            for ip in self.total_ip_list:
                p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
                if not p.match(ip):
                    msg = msg + "{}".format(ip)

            if msg != "Validate error :Below IP can not meet IP Address Format.\n":
                logger.error(msg)
                self.errors.append(msg)
                return True
            else:
                return self._validate_image_version()
        else:
            msg = "Validate error: Pls provide APIC/Switch IP configuration"
            logger.error(msg)
            self.errors.append(msg)
            return True

    def _validate_image_version(self):
        try:
            image32 = settings.global_policy['fabric']['global_policies']['switch_image32']
            image64 = settings.global_policy['fabric']['global_policies']['switch_image64']

            pattern_32 = r"^(.+)\.bin"
            pattern_64 = r'(.+)-cs_64.bin'

            if image32 == image64:
                if not image32.endswith(".bin"):
                    msg = "Validate error: Image name must end with .bin."
                    logger.error(msg)
                    return True
            else:
                if not re.match(pattern_32, image32).group(1) == re.match(pattern_64, image64).group(1):
                    msg = "Validate error: switch_image32 and switch_image64 checking failed."
                    logger.error(msg)
                    return True

        except Exception as e:
            msg = "Validate error: Yaml configuration switch_image32 and switch_image64 checking failed."
            logger.error(msg)
            msg = e
            logger.error(msg)
            self.errors.append(str(msg))
            return True

    def validate_ssh_telnet_connection(self):
        apic_error_msg = "Validate error: APIC CIMC SSH Fail.\n"
        apic_fail_list = []

        for ip in self.cimc_address:
            logger.info("Start SSH Connection Validate for {}, timeout 5 minustes".format(ip))
            connection_state = check_ssh_connection(ip, self.apic_cimc_credential[0], self.apic_cimc_credential[1])
            if not connection_state:
                apic_fail_list.append(ip)

        switch_error_msg = "Validate error: Switch Telnet Fail.\n"
        switch_fail_list = []

        for data in self.switch_list:
            connection_state = check_tennet_connection(data[0], data[1])
            if not connection_state:
                switch_fail_list.append("{}:{}".format(data[0], data[1]))

        if apic_fail_list and switch_fail_list:
            apic_error_msg += ",".join(apic_fail_list)
            switch_error_msg += ",".join(switch_fail_list)

            logger.error(apic_error_msg + '\n' + switch_error_msg)
            self.errors.append(switch_error_msg)
            return True

        if apic_fail_list and not switch_fail_list:
            apic_error_msg += ",".join(apic_fail_list)

            logger.error(apic_error_msg)
            self.errors.append(apic_error_msg)
            return True

        if not apic_fail_list and switch_fail_list:
            switch_error_msg += ",".join(switch_fail_list)

            logger.error(switch_error_msg)
            self.errors.append(switch_error_msg)
            return True

        logger.info("APIC CIMC SSH Connection and Switch Telnet Connection Success.")
        return

    def validate_apic_aaa_connection(self):
        apic_error_msg = "Validate error: APIC AAA Login Fail.\n"
        apic_fail_list = []

        for ip in self.apic_address:
            connection_state = apic_login(ip, self.aci_local_credential[0], self.aci_local_credential[1])
            if not connection_state:
                apic_fail_list.append(ip)

        if apic_fail_list:
            apic_error_msg += ",".join(apic_fail_list)
            logger.error(apic_error_msg)
            self.errors.append(apic_error_msg)
            return True

        logger.info("APIC AAA Login Connection Success.")
        return

    def validate_choices(self, value):
        from iac_init.conf import settings
        choices = value.split(',')
        if len(choices) == 1 and int(choices[0]) == 2:
            msg = 'Valid failed: Step 2 depends on step 1(Pls change input to 1,2)'
            logger.error(msg)
            self.errors.append(msg)
            return
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

    def validate_yaml_exist(self, yamlfile):
        for dir, _, files in os.walk(self.data_path):
            for filename in files:
                if yamlfile == filename:
                    self.yaml_path = os.path.join(dir, filename)
        if self.yaml_path:
            return self.yaml_path
        else:
            msg = "Vlidate Error: Yaml File {} not fount".format(yamlfile)
            logger.error(msg)
            self.errors.append(msg)
            return False

    def validate_cimc_precheck(self):
        cimc_username = self.apic_cimc_credential[0]
        cimc_password = self.apic_cimc_credential[1]
        result = {}
        for cimc_ip in self.cimc_address:
            error = cimc_precheck(cimc_ip, cimc_username, cimc_password)
            result[cimc_ip] = error

        result_state = True
        for cimc_ip, test_result in result.items():
            if test_result:
                msg = "{} pre-check success\n".format(cimc_ip)
                logger.info(msg)
            else:
                result_state = False
                msg = "{} pre-check fail\n".format(cimc_ip)
                logger.error(msg)

        if result_state:
            return False
        return True

    def _validate_bool(self, bool):
        if bool == "yes":
            pass
        else:
            exit(1)
