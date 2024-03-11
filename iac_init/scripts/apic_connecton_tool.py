# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import requests
import os
import json
import urllib3
from loguru import logger
from iac_init.conf import settings

logger.add(sink=os.path.join(settings.OUTPUT_BASE_DIR, 'iac_init_log', 'iac-init-main.log'), format="{time} {level} {message}", level="INFO")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_health_status(APIC_IP, token):
    try:
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Cookie': f'APIC-cookie={token}'
        }
        apic_health_url = f"https://{APIC_IP}/api/node/class/infraWiNode.json"
        response = requests.get(url=apic_health_url, headers=headers, verify=False)
        if response.status_code == 200:
            health_status = []
            return_data = response.json()
            for item in return_data['imdata']:
                health_status.append(item['infraWiNode']['attributes']['health'])
            for status in health_status:
                if status != "fully-fit":
                    msg = "Error: APIC {} Health Check fail(Not fully-fix)!!".format(APIC_IP)
                    logger.error(msg)
                    return False
            return True
        else:
            return False
    except Exception as e:
        msg = "{}".format(e)
        logger.error(msg)
        return False

def apic_login(APIC_IP, APIC_USERNAME, APIC_PASSWORD):
    try:
        apic_login_url = f"https://{APIC_IP}/api/aaaLogin.json"
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }

        data = {
            "aaaUser": {
                "attributes": {
                    "name": APIC_USERNAME,
                    "pwd": APIC_PASSWORD
                }
            }
        }
        response = requests.post(url=apic_login_url, headers=headers, data=json.dumps(data), verify=False)

        if response.status_code == 200:
            token = response.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
            if token:
                return get_health_status(APIC_IP, token)
            else:
                msg = "Error: APIC {} Connection Fail!!".format(APIC_IP)
                logger.error(msg)
                return False
        else:
            msg = "Error: APIC {} Connection Fail!!".format(APIC_IP)
            logger.error(msg)
            return False
    except Exception as e:
        msg = "{}".format(e)
        logger.error(msg)
        return False
