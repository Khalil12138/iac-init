# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import os
import time
import telnetlib
from loguru import logger
from iac_init.conf import settings

logger.add(
    sink=os.path.join(
        settings.OUTPUT_BASE_DIR,
        'iac_init_log',
        'iac-init-main.log'
    ),
    format="{time} {level} {message}",
    level="INFO"
)


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
            logger.warning(
                '{}:{} Network Connection Issue'
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
        print(command_result)
        if '#' in command_result:
            logger.info(
                '{}:{} Login Success!!'
                .format(self.host_ip, self.port)
            )
            self.tn.write(b"exit\n")
            self.tn.close()
            return True
        else:
            logger.warning(
                '{}:{} Login Failed wrong username or password'
                .format(self.host_ip, self.port)
            )
            self.tn.close()
            return False

