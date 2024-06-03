# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Wang Xiao <xiawang3@cisco.com>

import os
import time
import telnetlib

from iac_init.conf import settings
from iac_init.scripts.logging_tool import setup_logging


logger = setup_logging()


class TelnetClient:
    def __init__(
            self,
            telnet_ip,
            telnet_port,
            telnet_username,
            telnet_password
    ):
        self.tn = telnetlib.Telnet()
        self.host_ip = telnet_ip
        self.port = telnet_port
        self.username = telnet_username
        self.password = telnet_password

    def login_host(self):
        try:
            self.tn.open(self.host_ip, self.port)

        except:
            logger.error(
                '{}:{} connected failed!'
                .format(self.host_ip, self.port)
            )
            self.tn.close()
            return False

        self.tn.read_until(b'login: ', timeout=10)
        self.tn.write(self.username.encode('ascii') + b'\n')
        self.tn.read_until(b'Password: ', timeout=10)
        self.tn.write(self.password.encode('ascii') + b'\n')
        time.sleep(2)
        command_result = self.tn.read_very_eager()\
            .decode('ascii')
        # print(command_result)
        if 'Login incorrect' not in command_result:
            logger.info(
                'Login {}:{} successfully.'
                .format(self.host_ip, self.port)
            )
            self.tn.write(b"exit\n")
            self.tn.close()
            return True
        else:
            logger.error(
                'Login {}:{} failed due to wrong username or password!'
                .format(self.host_ip, self.port)
            )
            self.tn.close()
            return False
