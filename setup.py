#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = 'Mausbrand Informationssysteme GmbH'

import os
import sys

from setuptools import setup, find_packages

if sys.platform == "linux":
	try:
		xdg_data_dir = os.environ["${XDG_DATA_DIRS}"].split(":", 1)[0]
	except KeyError:
		if os.path.isdir("/usr/local/share"):
			xdg_data_dir = "/usr/local/share"
		elif os.path.isdir("/usr/share"):
			xdg_data_dir = "/usr/share"
		else:
			raise RuntimeError("Could not found xdg_data_dir and could not found a 'share' directory under /usr")
else:
	xdg_data_dir = None

setup(
		name='viur-admin',
		version='1.1',
		packages=find_packages(),
		zip_safe=False,
		setup_requires=sys.platform == "linux" and ['install_freedesktop'] or [],
		install_requires=["requests"],
		include_package_data=True,
		package_data={"": ["locales/*.qm"]},
		entry_points={
			"gui_scripts": [
				"viur_admin=viur_admin.admin:main"
			]
		},
		desktop_entries={
			'viur_admin': {
				'GenericName': 'Rich Client for viur server written in pyqt5',
				"Name": "Viur Admin",
				"Type": "Application",
				"Comment": "Admin App for Viur Server",
				"Categories": "Qt;Development;IDE;"
			},
		},
		data_files=sys.platform == "linux" and [
			(os.path.join(xdg_data_dir, "icons/hicolor/64x64/apps"), ['viur_admin/icons/viur_admin.png']),
		] or [],
		author="Mausbrand GmbH",
		author_email="info@mausbrand.de",
		description="pyqt5 admin tool for viur server",
		long_description="",
		license="GPL v3",
		keywords="",
		url="http://www.viur.is"
)
