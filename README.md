[![Tests](https://github.com/nac-aci/aac-init/actions/workflows/test.yml/badge.svg)](https://github.com/nac-aci/aac-init/actions/workflows/test.yml)
![Python Support](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-informational "Python Support: 3.8, 3.9, 3.10, 3.11, 3.12")

# aac-init

A CLI tool to bootstrap and configure ACI fabric using ACI as Code.

```bash
$ aac-init -h

Usage: aac-init [option] [arg] 

  A CLI tool to bootstrap and configure ACI fabric using ACI as Code.

Options:
  --version        print the aac-init version and exit.
  -d, --data PATH  Path to data YAML files.  [required]
  -h, --help       print this help message and exit.
```

All data from the YAML files (`--data` option) will first be combined into a single data structure which is then provided as input to the templating process. [TBD]

## Installation

Python 3.7+ is required to install `aac-init`. Don't have Python 3.7 or later? See [Python 3 Installation & Setup Guide](https://realpython.com/installing-python/).

`aac-init` can be installed in a virtual environment using `pip`:

```bash
pip install aac-init
```

## Usage(TBD)

```bash
$ aac-init -d /data
Select single or multiple option(s) to init ACI Fabric:
[1]  Wipe and boot APIC/switch to particular version(APIC + Switch)
[2]  APIC initial setup(Single Pod)
[3]  Init ACI Fabric via NaC(Network as Code)
Example: (1,2,..)
```

`Explain more here for Nac Templates`, supported NaC templates:


## Example(TBD)

## Updating

## Uninstallation

## FAQ

## Contact

[Xiao Wang](xiawang3@cisco.com)
[Rudy Lei](shlei@cisco.com)
