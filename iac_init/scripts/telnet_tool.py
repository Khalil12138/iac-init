# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import telnetlib

def check_tennet_connection(ip:str, port:int):
    try:
        telnetlib.Telnet(ip, port, timeout=5)
        return True
    except Exception:
        return False
