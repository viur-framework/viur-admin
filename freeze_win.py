# -*- coding: utf-8 -*-

import os.path

from cx_Freeze import setup, Executable

base = 'Win32GUI'

company_name = 'Mausbrand Informationssysteme GmbH'
product_name = 'ViurAdmin'

viur_admin_descr = 'The Viur Desktop Administration Tool'

shortcut_table = [
	(
		"DesktopShortcut",  # Shortcut
		"DesktopFolder",  # Directory_
		"ViurAdmin",  # Name
		"TARGETDIR",  # Component_
		"[TARGETDIR]admin.exe",  # Target
		None,  # Arguments
		viur_admin_descr,  # Description
		None,  # Hotkey
		None,  # Icon
		None,  # IconIndex
		None,  # ShowCmd
		'TARGETDIR'  # WkDir
	),
	(
		"StartupShortcut",  # Shortcut
		"StartupFolder",  # Directory_
		"ViurAdmin",  # Name
		"TARGETDIR",  # Component_
		"[TARGETDIR]admin.exe",  # Target
		None,  # Arguments
		viur_admin_descr,  # Description
		None,  # Hotkey
		None,  # Icon
		None,  # IconIndex
		None,  # ShowCmd
		'TARGETDIR'  # WkDir
	)
]

msi_data = {"Shortcut": shortcut_table}
bdist_msi_options = {
	'upgrade_code': '{5A11CF14-7ADE-4F1F-9B1A-9B34F6AF9EED}',
	'data': msi_data,
	'add_to_path': False,
	'initial_target_dir': r'[ProgramFilesFolder]\%s\%s' % (company_name, product_name)
}

executables = [
	Executable(
			os.path.join("viur_admin", "admin.py"),
			icon=os.path.join("viur_admin", "icons", "viur_win.ico"),
			base=base,
			shortcutName="ViurAdmin",
			shortcutDir="ProgramMenuFolder"
	)
]

options = {
	"build_exe": {
		"includes": ["atexit", "re", "PyQt5.QtPrintSupport"],
		"include_files": [
			"viur_admin/icons",
			"viur_admin/cacert.pem",
			"viur_admin/license.txt",
			"viur_admin/mime.types",
			"viur_admin/plugins",
			"viur_admin/locales"]
	},
	"bdist_msi": bdist_msi_options
}

setup(
		name='Viur Admin',
		version='0.99.1',
		description=viur_admin_descr,
		author=company_name,
		author_email='info@mausbrand.de',
		options=options,
		executables=executables
)
