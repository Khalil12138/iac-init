# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Wang Xiao <xiawang3@cisco.com>

import os
import re
import time
from ruamel import yaml

from loguru import logger
from typing import Any, Dict, List, Optional

from iac_init.conf import settings
from iac_init.yaml_conf.yaml import load_yaml_files
from iac_init.scripts.ssh_tool import check_ssh_connection
from iac_init.scripts.apic_connecton_tool import apic_login
from iac_init.scripts.cimc_precheck_tool import cimc_precheck
from iac_init.scripts.telnet_tool import TelnetClient

logger.add(sink=os.path.join(settings.OUTPUT_BASE_DIR,
           'iac_init_log', 'iac_init_main.log'),
           format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}',
           encoding='utf-8')


class Validator:
    def __init__(self, data_path: str, output: str):
        self.data: Optional[Dict[str, Any]] = None
        self.data_path = data_path
        self.output = output
        self.global_policy = None
        self.errors: List[str] = []
        self._wrapped = self._validate_path

    def _validate_path(self):
        '''Validate if user provided YAML directory exists'''
        if os.path.exists(self.data_path):
            if os.path.isdir(self.data_path):
                pass
            else:
                msg = "YAML directory must be a directory not a file: {}"\
                    .format(self.data_path)
                logger.error(msg)
                self.errors.append(msg)
                return True
        else:
            msg = "YAML Directory doesn't exist: {}".format(self.data_path)
            logger.error(msg)
            self.errors.append(msg)
            return True

        logger.info("Loaded YAML directory: {}".format(self.data_path))

        return self._validate_yaml()

    def _validate_syntax_file(self, file_path: str):
        """Run syntactic validation for a single file"""
        filename = os.path.basename(file_path)
        if os.path.isfile(file_path) \
                and \
                (".yaml" in filename or ".yml" in filename):
            logger.info("Validated file: {} successfully.".format(filename))

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
            msg = "Configuration File {} is missing!"\
                .format(settings.DEFAULT_DATA_PATH)
            logger.error(msg)
            self.errors.append(msg)
            return True

        return self._load_connnection_info()

    def _load_connnection_info(self):
        try:
            self.aci_local_credential = [
                settings.global_policy['fabric']['global_policies']
                ['aci_local_username'],
                settings.global_policy['fabric']['global_policies']
                ['aci_local_password']
            ]

            self.apic_cimc_credential = [
                settings.global_policy['fabric']['global_policies']
                ['apic_cimc_username'],
                settings.global_policy['fabric']['global_policies']
                ['apic_cimc_password']
            ]

            self.apic_address = [
                data['apic_address']
                for data in
                settings.global_policy['fabric']['apic_nodes_connection']
            ]

            self.cimc_address = [
                data['cimc_address']
                for data in
                settings.global_policy['fabric']['apic_nodes_connection']
            ]

            self.switch_list = [
                [data['console_address'], data['console_port']]
                for data in settings.global_policy['fabric']
                ['switch_nodes_connection']
            ]

            self.total_ip_list = self.apic_address + self.cimc_address

            con = settings.global_policy['fabric']['switch_nodes_connection']

            self.total_ip_list += [data['console_address'] for data in con]

            settings.cimc_list = self.cimc_address
            settings.apic_list = self.apic_address
            settings.aci_local_credential = self.aci_local_credential
            settings.apic_cimc_credential = self.apic_cimc_credential
            settings.switch_list = \
                [':'.join(map(str, item)) for item in self.switch_list]

            return self._validate_ip()

        except Exception as e:
            msg = e
            logger.error(msg)
            self.errors.append(str(msg))
            return True

    def _validate_ip(self):
        pattern = r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.)' \
                  r'{3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$'
        fail_ip_list = []
        if self.total_ip_list:
            msg = "Validation Error: " \
                  "Below IP(s) can not meet IP Address Format!\n"
            for ip in self.total_ip_list:
                p = re.compile(pattern)
                if not p.match(ip):
                    fail_ip_list.append(ip)
                    msg = msg + "{}".format(ip)

            if fail_ip_list:
                logger.error(msg)
                self.errors.append(msg)
                return True
            else:
                return self._validate_image_version()
        else:
            msg = "Validation error: APIC/Switch IP configuration is missing!"
            logger.error(msg)
            self.errors.append(msg)
            return True

    def _validate_image_version(self):
        try:
            global_policy = settings.global_policy['fabric']['global_policies']
            image32 = global_policy['switch_image32']
            image64 = global_policy['switch_image64']

            pattern_32 = r"^(.+)\.bin"
            pattern_64 = r'(.+)-cs_64.bin'

            if image32 == image64:
                if not image32.endswith(".bin"):
                    msg = "Validation error: Image name must end with .bin."
                    logger.error(msg)
                    return True
            else:
                if not re.match(pattern_32, image32).group(1) == \
                       re.match(pattern_64, image64).group(1):
                    msg = "Validation error: switch_image32 and " \
                          "switch_image64 are not in same release!"
                    logger.error(msg)
                    return True

        except Exception as e:
            msg = "Validation error: YAML configuration switch_image32 and " \
                  "switch_image64 checking failed!"
            logger.error(msg)
            msg = e
            logger.error(msg)
            self.errors.append(str(msg))
            return True

    def validate_ssh_telnet_connection(self):
        apic_error_msg = "Validation error: APIC CIMC SSH failed!\n"
        apic_fail_list = []

        for ip in self.cimc_address:
            logger.info("Start SSH connection validation for {}, "
                        "timeout 5 minutes".format(ip))
            connection_state = check_ssh_connection(
                ip,
                self.apic_cimc_credential[0],
                self.apic_cimc_credential[1]
            )
            if not connection_state:
                apic_fail_list.append(ip)

        switch_error_msg = "Validation error: Switch Telnet failed!\n"
        switch_fail_list = []

        for data in self.switch_list:
            logger.info("Start Telnet connection validation for {}:{}"
                        .format(data[0], data[1]))
            connection = TelnetClient(
                data[0],
                data[1],
                self.aci_local_credential[0],
                self.aci_local_credential[1]
            )
            connection_state = connection.login_host()
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

        logger.info("APIC CIMC SSH connection and "
                    "Switch Telnet connection validate successfully.")
        return

    def validate_apic_aaa_connection(self):
        # Rudy: Need to update AAA login code later
        # (it's default domain at this moment)
        apic_error_msg = "Validatation error: APIC Login failed!\n"
        apic_fail_list = []

        for ip in self.apic_address:
            start_time = time.time()
            if apic_fail_list:
                apic_fail_list = list[set(apic_fail_list)]
                apic_error_msg += ",".join(apic_fail_list)
                logger.error(apic_error_msg)
                self.errors.append(apic_error_msg)
                return True

            i = 1
            while True:
                # Totally run 900 seconds every 3 seconds
                # test if APIC could AAA login.
                if time.time() - start_time >= 900:
                    break
                connection_state = apic_login(
                    ip,
                    self.aci_local_credential[0],
                    self.aci_local_credential[1]
                )
                if not connection_state:
                    apic_fail_list.append(ip)
                    logger.info("Attempt to validate {} "
                                "APIC Login Connection {}th,"
                                " timeout 15 mins."
                                .format(ip, i))
                    i += 1
                    time.sleep(3)
                else:
                    break

        logger.info("APIC Login validates successfully.")
        return

    def validate_choices(self, value):
        from iac_init.conf import settings
        choices = value.split(',')
        valid_choices = list(str(i) for i in
                             range(1, len(settings.DEFAULT_USER_OPTIONS)+1)
                             )
        for choice in choices:
            if choice not in valid_choices:
                msg = '{} is not a valid choice!'.format(choice)
                logger.error(msg)
                self.errors.append(msg)
                return
        self.choices = sorted(choices, key=lambda x: int(x))
        self.options = value
        return self.choices

    # This function is used for option 1 and 2.
    # Rudy: seems this is used for all options
    def validate_yaml_exist(self, yamlfile):
        for dir, _, files in os.walk(self.data_path):
            for filename in files:
                if yamlfile == filename:
                    self.yaml_path = os.path.join(dir, filename)
        if self.yaml_path:
            msg = "YAML file {} validated successfully.".format(yamlfile)
            logger.info(msg)
            return self.yaml_path
        else:
            msg = "Validation error: YAML file {} is missing!".format(yamlfile)
            logger.error(msg)
            self.errors.append(msg)
            return False

    # This function is used for option 3.
    def validate_yaml_dir_exist(self, yaml_dir):
        try:
            self.file_dir_list = []
            folder_path = os.path.join(self.data_path, yaml_dir)
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                for dir, _, files in os.walk(folder_path):
                    for filename in files:
                        option3_yaml_path = os.path.join(dir, filename)
                        if option3_yaml_path:
                            self.file_dir_list.append(option3_yaml_path)
            else:
                msg = "Validation Error: Directory {} doesn't exist!"\
                    .format(folder_path)
                logger.error(msg)
                self.errors.append(msg)
                return False

            if self.file_dir_list:
                return self.file_dir_list
            else:
                msg = "Validation Error: No file found in dir: {}"\
                    .format(folder_path)
                logger.error(msg)
                self.errors.append(msg)
                return False
        except Exception as e:
            msg = "Validation Error: {}".format(e)
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
                msg = "APIC CIMC {} pre-check successfully.\n".format(cimc_ip)
                logger.info(msg)
            else:
                result_state = False
                msg = "APIC CIMC {} pre-check failed!\n".format(cimc_ip)
                logger.error(msg)

        if result_state:
            return False
        return True

    def _validate_bool(self, bool):
        if bool == "yes":
            pass
        else:
            exit(1)

    def write_output(self, input_paths: List[str], path: str):
        if self.data is None:
            self.data = load_yaml_files(input_paths)
        try:
            with open(path, "w") as fh:
                y = yaml.YAML()
                y.default_flow_style = False
                y.dump(self.data, fh)
            return True

        except:
            logger.error("Cannot write file: {}".format(path))
            return False
