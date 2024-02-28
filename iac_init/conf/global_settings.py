# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

APIC_DEVICES = []
APIC_USERNAME = ""
APIC_PASSWORD = ""

MULTIPLE_DEVICE = False

DEFAULT_USER_OPTIONS = [
    "APIC/Switch PXE boot up.",
    "Fabric discovery.(Single Pod, Multi Pod, Multi Site, Remote Leaf, etc..)",
    "Management Configuration.(INB, OOB, NTP, DNS, AAA, etc..)",
    "Fabric policy creation.",
    "Access policy creation.",
    "Fabric features.(SNMP, syslog, etc..)"
]

DEFAULT_DATA_PATH = {
    'PXE_Boot': "./data/pxe_boot.sh",
    'Fabric_discovery': "./data/pxe_boot.sh"
}
