# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Rudy Lei <shlei@cisco.com>

# This is for APIC CIMC pre check, run this pre check when option 1 is selected, apply this for all APICs.


import os
import re
import urllib3
import requests
import xml.etree.ElementTree as ET

from loguru import logger
from iac_init.conf import settings

logger.add(sink=os.path.join(settings.OUTPUT_BASE_DIR, 'iac_init_log', 'iac-init-main.log'), format="{time} {level} {message}", level="INFO")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def cimc_api(CIMC_IP, data):
    try:
        cimc_url = f"https://{CIMC_IP}/nuova"
        headers = {
            'accept': '*/*',
            'Content-Type': 'text/html',
        }

        response = requests.post(url=cimc_url, headers=headers, data=data, verify=False)

        if response.status_code == 200:
            return response
        else:
            msg = f"Error: CIMC {CIMC_IP} Connection Fail!!"
            logger.error(msg)
            return False
    except Exception as e:
        msg = "{}".format(e)
        logger.error(msg)
        return False

def cimc_login(CIMC_IP, CIMC_USERNAME, CIMC_PASSWORD):
    try:
        data = f"<aaaLogin inName='{CIMC_USERNAME}' inPassword='{CIMC_PASSWORD}'></aaaLogin>"
        response = cimc_api(CIMC_IP, data)
        token = ET.fromstring(response.text).attrib['outCookie']
        if token:
            logger.info(f"Login token: {token}")
            return token
        else:
            msg = f"Error: CIMC {CIMC_IP} Login Fail!!"
            logger.error(msg)
            return False

    except Exception as e:
        msg = "{}".format(e)
        logger.error(msg)
        return False

def cimc_logout(CIMC_IP, token):
    try:
        data = f"<aaaLogout cookie='{token}' inCookie='{token}'> </aaaLogout>"
        response = cimc_api(CIMC_IP, data)
        logger.info(f"Logout {token} successfully!")

    except Exception as e:
        msg = "{}".format(e)
        logger.error(msg)
        return False

def cimc_health_check(CIMC_IP, token):
    try:
        firmware_data = f'''
        <!-- firmware version -->
        <configResolveDn cookie="{token}" inHierarchical='false' dn="sys/rack-unit-1/mgmt/fw-system"/>
        '''
        firmware_response = cimc_api(CIMC_IP, firmware_data)
        logger.info(firmware_response.text)
        firmware_version = ET.fromstring(firmware_response.text).find('.//firmwareRunning').attrib['version']
        logger.info(f"Current Firmware version is: {firmware_version}")

        fault_data = f'''
        <!-- fault info -->
        <configResolveClass cookie="{token}" inHierarchical='false' classId='faultInst'/>
        '''
        logger.info("Logging CIMC fault info:")
        fault_response = cimc_api(CIMC_IP, fault_data)
        logger.info(fault_response.text)

        tpm_data = f'''
        <!-- TPM status -->
        <configResolveClass cookie="{token}" inHierarchical='false' classId='equipmentTpm'/>
        '''
        tpm_response = cimc_api(CIMC_IP, tpm_data)
        logger.info(tpm_response.text)
        tpm_status = ET.fromstring(tpm_response.text).find('.//equipmentTpm').attrib['enabledStatus']
        logger.info(f"Current TPM status is: {tpm_status}")

        if "enable" not in tpm_status:
            logger.error("TPM is not enabled!!")
            return False

        return True

    except Exception as e:
        msg = "{}".format(e)
        logger.error(msg)
        return False

def cimc_mapping_clean(CIMC_IP, token):
    try:
        cimc_mapping_data = f'''
        <!-- Retrieve CIMC mapping -->
        <configResolveClass cookie="{token}" inHierarchical='false' classId='commVMediaMap'/>
        '''
        cimc_mapping_response = cimc_api(CIMC_IP, cimc_mapping_data)
        logger.info(cimc_mapping_response.text)
        if re.search(r'commVMediaMap volumeName', cimc_mapping_response.text):
            existing_mapping = ET.fromstring(cimc_mapping_response.text).find('.//commVMediaMap').attrib['volumeName']
            logger.info(f"Removing existing mapping: {existing_mapping}")
            cimc_mapping_clear_data = f'''
            <!-- CIMC mapping clear -->
            <configConfMo cookie="{token}"><inConfig>
                <commVMediaMap  dn="sys/svc-ext/vmedia-svc/vmmap-{existing_mapping}" volumeName="{existing_mapping}" status='removed' ></commVMediaMap>
            </inConfig></configConfMo>
            '''
            cimc_mapping_clear_response = cimc_api(CIMC_IP, cimc_mapping_clear_data)
            if cimc_mapping_clear_response:
                logger.info(f"Removed existing mapping: {existing_mapping}")
            else:
                return False

        cimc_boot_data = f'''
        <!-- Retrieve CIMC boot order -->
        <configResolveClass cookie="{token}" inHierarchical='false' classId='lsbootVMedia'/>
        '''
        cimc_boot_data_response = cimc_api(CIMC_IP, cimc_boot_data)
        logger.info(cimc_boot_data_response.text)
        if re.search(r'lsbootVMedia name', cimc_boot_data_response.text):
            existing_bootorder = ET.fromstring(cimc_boot_data_response.text).find('.//lsbootVMedia').attrib['name']
            logger.info(f"Removing existing boot order: {existing_bootorder}")
            cimc_bootorder_clear_data = f'''
            <!-- CIMC boot order clear -->
            <configConfMo cookie="{token}"><inConfig>
                <lsbootVMedia  dn="sys/rack-unit-1/boot-precision/vm-{existing_bootorder}" name="{existing_bootorder}" status='removed' ></lsbootVMedia>
            </inConfig></configConfMo>
            '''
            cimc_bootorder_clear_response = cimc_api(CIMC_IP, cimc_bootorder_clear_data)
            if cimc_bootorder_clear_response:
                logger.info(f"Removed existing boot order: {existing_bootorder}")
            else:
                return False

        return True

    except Exception as e:
        msg = "{}".format(e)
        logger.error(msg)
        return False

def power_down_cimc(CIMC_IP, token):
    try:
        cimc_power_down_data = f'''
        <!-- CIMC Power Off -->
        <configConfMo cookie="{token}"><inConfig>
            <computeRackUnit dn="sys/rack-unit-1" adminPower="down" />
        </inConfig></configConfMo>
        '''
        cimc_power_down_response = cimc_api(CIMC_IP, cimc_power_down_data)
        if cimc_power_down_response:
            logger.info("CIMC is powered down.")
        else:
            return False

        return True

    except Exception as e:
        msg = "{}".format(e)
        logger.error(msg)
        return False

def cimc_precheck(CIMC_IP, CIMC_USERNAME, CIMC_PASSWORD):
    try:
        token = cimc_login(CIMC_IP, CIMC_USERNAME, CIMC_PASSWORD)
        health_check_result = cimc_health_check(CIMC_IP, token)
        if not health_check_result:
            logger.error("CIMC health check failed!!")
            return False

        logger.info("CIMC health check pass!")

        cimc_mapping_clean_result = cimc_mapping_clean(CIMC_IP, token)
        if not cimc_mapping_clean_result:
            logger.error("CIMC mapping clean failed!!")
            return False

        logger.info("CIMC mapping clean successfully!")
        logger.info("Powering down CIMC...")
        power_down_cimc(CIMC_IP, token)
        cimc_logout(CIMC_IP, token)
        
        return True

    except Exception as e:
        msg = "{}".format(e)
        logger.error(msg)
        return False
