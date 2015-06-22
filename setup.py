#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = 'stefan'

from setuptools import setup

setup(
    name='viur-admin',
    version='0.1',
    packages=["viur_admin"],
    zip_safe=False,
    # install_requires=["requests"],
    include_package_data=True,
    package_data={"": ["locales/*.qm"]},
    entry_points="""
    [console_scripts]
    viur_admin = viur_admin.admin:main
    """,
    author="Mausbrand GmbH",
    author_email="info@mausbrand.de",
    description="pyqt5 admin tool for viur server",
    long_description="",
    license="GPL v3",
    keywords="",
    url=""
)
