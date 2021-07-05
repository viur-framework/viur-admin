from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.

shortcut_table = [
	("DesktopShortcut",  # Shortcut
	 "DesktopFolder",  # Directory_
	 "program",  # Name
	 "TARGETDIR",  # Component_
	 "[TARGETDIR]main.exe",  # Target
	 None,  # Arguments
	 None,  # Description
	 None,  # Hotkey
	 None,  # Icon
	 None,  # IconIndex
	 None,  # ShowCmd
	 'TARGETDIR'  # WkDir
	 ),

	("StartupShortcut",  # Shortcut
	 "StartupFolder",  # Directory_
	 "program",  # Name
	 "TARGETDIR",  # Component_
	 "[TARGETDIR]main.exe",  # Target
	 None,  # Arguments
	 None,  # Description
	 None,  # Hotkey
	 None,  # Icon
	 None,  # IconIndex
	 None,  # ShowCmd
	 'TARGETDIR'  # WkDir
	 ),

]

msi_data = {"Shortcut": shortcut_table}  # This will be part of the 'data' option of bdist_msi

includes = ["atexit", "PyQt5.QtPrintSupport"]
includefiles = [r"viur_admin/resources/viur.ico", r"viur_admin/resources/cacert.pem"]

buildOptions = dict(packages=[], excludes=[], includes=includes, include_files=includefiles, include_msvcr=True)

import sys

base = 'Win32GUI' if sys.platform == 'win32' else None

company_name = 'Mausbrand Informationssysteme GmbH'
product_name = 'Viur Admin'

bdist_msi_options = {
	'upgrade_code': '{66620F3A-DC3A-11E2-B341-002219E9B01E}',
	'add_to_path': False,
	'initial_target_dir': r'[ProgramFilesFolder]\%s\%s' % (company_name, product_name),
	'data': msi_data
}

executables = [
	Executable(
		'viur_admin/admin.py',
		base=base,
		targetName='viurAdmin.exe',
		icon=r"viur_admin/icons/viur_win.ico",
		shortcutName="ViurAdmin",
		shortcutDir="ProgramMenuFolder")
]

setup(
	name='ViurAdmin',
	author="Mausbrand Informationssysteme GmbH",
	author_email="info@mausbrand.de",
	version='1.0',
	description='Content Management application for written in Qt5',
	options=dict(build_exe=buildOptions, bdist_msi=bdist_msi_options),
	executables=executables)
