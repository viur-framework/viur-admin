#!/usr/bin/python3
# -*- coding: utf-8 -*-
import glob
from subprocess import Popen

__author__ = 'Stefan Kögl'

import os
import os.path
import shutil

resourceToCopy = [
	"cacert.pem",
	"app.css",
	"icons.qrc",
]


def createResourceFile(projectPath, iconPath):
	for i in resourceToCopy:
		shutil.copyfile(os.path.join(projectPath, i), os.path.join(iconPath, i))

	tpl = """<RCC>\n    <qresource prefix="icons">\n{0}\n    </qresource>\n    <qresource>\n{1}\n    </qresource>\n</RCC>\n"""

	iconFiles = list()

	os.chdir(iconPath)

	for root, dirs, files in os.walk(iconPath):
		for i in files:
			if not i.startswith("."):
				absPath = os.path.join(root, i)
				relPath = os.path.relpath(absPath, iconPath)
				print("absPath, relPath:", absPath, relPath)
				iconFiles.append(relPath)

	try:
		shutil.copytree(
			os.path.join(projectPath, "htmleditor"),
			os.path.join(iconPath, "htmleditor"))
	except:
		pass

	htmleditorPath = os.path.join(iconPath, "htmleditor")
	editorFiles = list()
	for root, dirs, files in os.walk(htmleditorPath):
		for i in files:
			if not i.startswith("."):
				absPath = os.path.join(root, i)
				relPath = os.path.relpath(absPath, iconPath)
				editorFiles.append(relPath)

	os.chdir(projectPath)
	# for i in resourceToCopy:
	# 	os.remove(os.path.join(iconPath, i))
	# shutil.rmtree(os.path.join(iconPath, "htmleditor"))
	fp = open("resources_tmp.qrc", "w")
	iconFiles.sort()
	editorFiles.sort()
	iconTxt = "\n".join(["        <file>{0}</file>".format(i) for i in iconFiles])
	editorTxt = "\n".join(["        <file>{0}</file>".format(i) for i in editorFiles])
	fp.write(tpl.format(iconTxt, editorTxt))
	os.chdir(projectPath)


def convertImage(iconPath: str):
	pd = Popen(["convert", "filetypes/jpg.svg", "filetypes/jpg.png"], cwd=iconPath)
	pd.communicate()


def generateResource(iconPath: str):
	pd = Popen("pyrcc5 icons.qrc -o ../ui/icons_rc.py", cwd=iconPath)
	pd.communicate()
	shutil.copyfile(
		os.path.join(os.path.dirname(iconPath), "icons_rc.py"),
		os.path.join(iconPath, "icons_rc.py"),
	)


def updateTranslations(projectPath: str):
	pd = Popen("pylupdate5 -noobsolete viur_admin.pro", cwd=projectPath)
	pd.communicate()


def generateUiFiles(uiPath: str):
	os.chdir(uiPath)
	for i in glob.glob("*.ui"):
		tmpName = "{0}UI.py".format(os.path.splitext()[0])
		pd = Popen("pyuic5 {0} -o {1}".format(i, tmpName))
		pd.communicate()
		open(tmpName, "w").write(open(tmpName).read().replace(
			"import icons_rc",
			"import viur_admin.ui.icons_rc"
		))


def createQtProjectFile():
	fd = open("viur_admin_test.pro", "w")
	forms = list()
	sources = list()
	translations = list()
	extmap = {
		'.ui': ("FORMS +=", forms),
		'.py': ("SOURCES +=", sources),
		'.ts': ("TRANSLATIONS +=", translations),
	}

	for root, directories, files in os.walk("viur_admin"):
		if root.startswith("viur_admin/plugins") or root.endswith("__pycache__"):
			continue
		print("root", root)
		for entry in files:
			_, extention = os.path.splitext(entry)
			try:
				prefix, destList = extmap.get(extention)
				tmp = "{0} {1}\n".format(prefix, os.path.join(root, entry))
				if tmp not in destList:
					destList.append(tmp)
			except Exception as err:
				pass

	fd.writelines(forms)
	fd.writelines(sources)
	fd.writelines(translations)


if __name__ == '__main__':
	projectPath = os.getcwd()
	iconPath = os.path.join(projectPath, "viur_admin", "icons")
	uiPath = os.path.join(projectPath, "viur_admin", "ui")
	createQtProjectFile()
	updateTranslations(projectPath)
	convertImage(iconPath)
	createResourceFile(projectPath, iconPath)
	generateResource(iconPath)
	generateUiFiles(uiPath)
