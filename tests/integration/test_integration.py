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

    inputs = iter(['3', 'yes'])

    def mock_input(prompt):
        return next(inputs)

    monkeypatch.setattr('builtins.input', mock_input)

    result = runner.invoke(
        iac_init.cli.main.main,
        ["-d", yaml_path]
    )

    assert result.exit_code == 0  # Check  if  the  command  ran  successfully
    assert result.output.strip() == "IAC  initialization  completed  successfully."  # Check  output  message

