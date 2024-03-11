# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import click

yaml_dir_path = click.option('--data', '-d', type=click.Path(), required=True, help='Path to data YAML files.')
