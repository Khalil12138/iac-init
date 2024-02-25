# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import click

path = click.option('--fabric-config', '-f', type=click.Path(), required=True, help='Path to fabric configuration file')
