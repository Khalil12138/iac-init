# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Wang Xiao <xiawang3@cisco.com>

import os.path
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_BASE_DIR = os.path.join(os.getcwd(), "iac_init_output_working_dir")

DEFAULT_USER_OPTIONS = [
    "Wipe and boot APIC/switch to particular version(APIC + Switch)",
    "APIC initial setup(Single Pod)",
    "Init ACI Fabric via NaC(Network as Code)"
]


DEFAULT_DATA_PATH = "00-global_policy.yml"

DATA_PATH = [
    "00-global_policy.yml",
    "00-global_policy.yml",
    "nac_data",
]

TEMPLATE_DIR = [
    os.path.join(BASE_DIR, "templates", "01-wipe_aci_fabric"),
    os.path.join(BASE_DIR, "templates", "02-discover_apic"),
    os.path.join(BASE_DIR, "templates", "03-nac_tasks"),
]

OUTPUT_DIR = [
    os.path.join(OUTPUT_BASE_DIR, "01-wipe_aci_fabric"),
    os.path.join(OUTPUT_BASE_DIR, "02-discover_apic"),
    os.path.join(OUTPUT_BASE_DIR, "03-nac_tasks"),
]

os.environ["iac_init_option_1"] = OUTPUT_DIR[0]
os.environ["iac_init_option_2"] = OUTPUT_DIR[1]

# Rudy: sync the step name later
ANSIBLE_STEP = [
    'iac-validate',
    'deploy',
    'iac-test',
    'wipe_apic',
    'wipe_switch',
    'apic_setup'
]
