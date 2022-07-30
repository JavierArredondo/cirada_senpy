#!/usr/bin/env python

from cirada_senpy import __version__
from setuptools import find_packages, setup

with open("requirements.txt") as f:
    required_packages = f.readlines()

setup(
    name="cirada_senpy",
    version=__version__,
    description="CIRADA Cutout SErvice iN PYthon",
    author="JavierArredondo",
    author_email="javier.arredondo.c@usach.cl",
    include_package_data=True,
    packages=find_packages(),
    install_requires=required_packages,
    build_requires=required_packages,
    entry_points={
        "console_scripts": [
            "senpy = cirada_senpy.cli.commands:cli",
        ],
    },
    project_urls={
        "Github": "https://github.com/JavierArredondo/CIRADA_SENPY",
        "Documentation": "",
    },
)
