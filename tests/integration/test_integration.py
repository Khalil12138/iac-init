# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Daniel Schmidt <danischm@cisco.com>

import os
import pytest

from click.testing import CliRunner

import iac_init.cli.main

pytestmark = pytest.mark.integration


def test_iac_init(monkeypatch):
    runner = CliRunner()
    yaml_path = os.path.join("test", "integration", "fixtures", "data")

    result = runner.invoke(
        iac_init.cli.main.main,
        ["-d", yaml_path],
        input='3\nyes'
    )

    # Check if the command ran successfully
    assert result.exit_code == 0
