# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import os.path
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_BASE_DIR = os.path.join(".", "iac_init_output_working_dir")

DEFAULT_USER_OPTIONS = [
    "Wipe an ACI fabric/PXE boot(APIC + Switch).",
    "Discovery an ACI fabric APIC(Single Pod, MultiPod, MultiSite, RemoteLeaf).",
    "ACI fabric Node Registration(NaC starts from here).",
    "Configure ACI OOB Mgmt address.",
    "Configure ACI system settings.",
    "Configure Fabric Policies.",
    "Configure Access Policies.",
    "Configure ACI INB Mgmt address(Step 7th is required).",
    "Configure Smart Licensing.",
    "Configure ACI AAA(TACACS+, RADIUS, LDAP, etc..).",
    "Configure Monitor(Syslog, SNMP, Callhome).",
    "Configuration Backup."
]

DEFAULT_DATA_PATH = "00-global_policy.yml"

DATA_PATH = [
    "00-global_policy.yml",
    "00-global_policy.yml",
    "03-node_registration.yml",
    "04-oob_mgmt.yml",
    "05-aci_system_settings.yml",
    "06-fabric_policy.yml",
    "07-access_policy.yml",
    "08-inb_mgmt.yml",
    "09-smart_licensing.yml",
    "10-confg_aaa.yml",
    "11-config_monitor.yml",
    "12-config_backup.yml"
]

TEMPLATE_DIR = [
    os.path.join(BASE_DIR, "templates", "01-wipe_aci_fabric"),
    os.path.join(BASE_DIR, "templates", "02-discover_apic"),
    os.path.join(BASE_DIR, "templates", "03-node_registration"),
    os.path.join(BASE_DIR, "templates", "04-oob_mgmt"),
    os.path.join(BASE_DIR, "templates", "05-aci_system_settings"),
    os.path.join(BASE_DIR, "templates", "06-fabric_policy"),
    os.path.join(BASE_DIR, "templates", "07-access_policy"),
    os.path.join(BASE_DIR, "templates", "08-inb_mgmt"),
    os.path.join(BASE_DIR, "templates", "09-smart_licensing"),
    os.path.join(BASE_DIR, "templates", "10-confg_aaa"),
    os.path.join(BASE_DIR, "templates", "11-config_monitor"),
    os.path.join(BASE_DIR, "templates", "12-config_backup")
]

ANSIBLE_STEP = [
    'iac-validate',
    'deploy',
    'iac-test'
]
