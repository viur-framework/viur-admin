__author__ = 'stefan'

__version__ = [2, 3, 0]
from viur_admin.pyodidehelper import isPyodide
if isPyodide:
	print("Pyodide-main")
	from viur_admin.ui import icons_rc
	from viur_admin.admin import main
	_ = main()
