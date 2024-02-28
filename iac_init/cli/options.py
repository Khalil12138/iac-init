# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import click

path = click.option('--data', '-d', type=click.Path(), required=True, help='Path to data YAML files.')

settings_path = click.option('--settings', '-s', type=click.Path(), required=True, help='Path to user config settings.py')
