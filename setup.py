#!/usr/bin/env python

from setuptools import setup, find_packages
from cirada_senpy import __version__

with open("requirements.txt") as f:
    required_packages = f.readlines()

setup(
    name="cirada_senpy",
    version=__version__,
    description="CIRADA Cutout SErvice iN PYthon",
    author="JavierArredondo",
    author_email="javier.arredondo.c@usach.cl",
    packages=find_packages(),
    install_requires=required_packages,
    build_requires=required_packages,
    project_urls={
        "Github": "https://github.com/JavierArredondo/CIRADA_SENPY",
        "Documentation": "",
    },
)
