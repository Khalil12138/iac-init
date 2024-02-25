import importlib
import importlib.util
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class Initiator:
    def __init__(self, ip_config_path: str):
        self.data: Optional[Dict[str, Any]] = None
        if os.path.exists(ip_config_path) and os.path.isfile(ip_config_path):
            self.ip_config_path = ip_config_path
            logger.info("Loading APIC Fabric IP Config File")
            with open(ip_config_path) as f:
                self.path = f.readlines()
        else:
            logger.error("APIC Fabric IP Config File not found: {}".format(ip_config_path))
            sys.exit(1)
        self.errors: List[str] = []

    def _validate_ip_config(self) -> None:
        """Run APIC IP Addresses validation for Fabric IP Configuration file"""
        logger.info("Validate APIC IP Configuration file: %s", self.path)
        if not self.path:
            msg = "Validate error '{}': No Content in configuration file".format(self.path)
            logger.error(msg)
            self.errors.append(msg)
            return

        line_number = 0
        msg = "Validate error '{}': Can not meet IP Address Format.\n".format(self.ip_config_path)
        for line in self.path:
            line_number += 1
            p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
            if not p.match(line.strip('\n')):
                msg = msg + "Line {}: {}".format(line_number, line)
        if msg != "Validate error '{}' can not meet IP Address Format\n".format(self.ip_config_path):
            logger.error(msg)
            self.errors.append(msg)
            return
