#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
import glob
from subprocess import Popen, PIPE

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
	mainCodePath = os.path.join(projectPath, "viur_admin")
	for i in resourceToCopy:
		shutil.copyfile(
			os.path.join(mainCodePath, i),
			os.path.join(iconPath, i)
		)

	tpl = """<RCC>\n    <qresource prefix="icons">\n{0}\n    </qresource>\n    <qresource>\n{1}\n    </qresource>\n</RCC>\n"""

	iconFiles = list()

	os.chdir(iconPath)

	for root, dirs, files in os.walk(iconPath):
		for i in files:
			if not i.startswith(".") and i != "icons.qrc" and i != "icons_rc.py":
				absPath = os.path.join(root, i)
				relPath = os.path.relpath(absPath, iconPath)
				print("absPath, relPath:", absPath, relPath)
				iconFiles.append(relPath)

	try:
		shutil.copytree(
			os.path.join(projectPath, "viur_admin", "htmleditor"),
			os.path.join(iconPath, "htmleditor"))
	except Exception as err:
		print(err)
		pass

	htmleditorPath = os.path.join(iconPath, "htmleditor")
	editorFiles = list()
	for root, dirs, files in os.walk(htmleditorPath):
		for i in files:
			if not i.startswith("."):
				absPath = os.path.join(root, i)
				relPath = os.path.relpath(absPath, iconPath)
				editorFiles.append(relPath)



	print("creating qrc file?", mainCodePath, "icons.qrc")
	fp = open(os.path.join(mainCodePath, "icons.qrc"), "w")
	iconFiles.sort()
	editorFiles.sort()
	iconTxt = "\n".join(["        <file>{0}</file>".format(i) for i in iconFiles])
	editorTxt = "\n".join(["        <file>{0}</file>".format(i) for i in editorFiles])
	fp.write(tpl.format(iconTxt, editorTxt))
	fp.flush()
	fp.close()
	del fp
	print("generateResource", iconPath)
	pd = Popen("pyrcc5 icons.qrc -o ../ui/icons_rc.py", cwd=iconPath, shell=True, stdout=PIPE, stderr=PIPE)
	print(pd.communicate())
	shutil.copyfile(
		os.path.join(os.path.dirname(iconPath), "ui", "icons_rc.py"),
		os.path.join(iconPath, "icons_rc.py"),
	)

	os.chdir(projectPath)
	for i in resourceToCopy:
		os.remove(os.path.join(iconPath, i))
	shutil.rmtree(os.path.join(iconPath, "htmleditor"))


def convertImage(iconPath: str):
	pd = Popen(["convert", "filetypes/jpg.svg", "filetypes/jpg.png"], cwd=iconPath)
	pd.communicate()


def generateResource(iconPath: str):
	pass


def updateTranslations(projectPath: str):
	pd = Popen("pylupdate5 -noobsolete viur_admin.pro", cwd=projectPath, shell=True)
	pd.communicate()


def generateUiFiles(uiPath: str):
	os.chdir(uiPath)
	for i in glob.glob("*.ui"):
		tmpName = "{0}UI.py".format(os.path.splitext(i)[0])
		cmd = "pyuic5 {0} -o {1}".format(i, tmpName)
		print("cmd", cmd)
		pd = Popen(cmd, cwd=uiPath, shell=True, stderr=PIPE, stdout=PIPE)
		print("generateUiFiles results", pd.communicate())
		tmp = open(tmpName).read().replace(
			"import icons_rc",
			"import viur_admin.ui.icons_rc"
		)
		open(tmpName, "w").write(tmp)


def createQtProjectFile(projectPath: str):
	"""Here we're generating a qt project file which we'll later need for creating translation files (*.ts)

	:param projectPath:
	:return:
	"""
	fd = open(os.path.join(projectPath, "viur_admin.pro"), "w")
	forms = list()
	sources = list()
	translations = list()
	extmap = {
		'.ui': ("FORMS +=", forms),
		'.py': ("SOURCES +=", sources),
		'.ts': ("TRANSLATIONS +=", translations),
	}

	mainCodeDirectory = os.path.join(projectPath, "viur_admin")
	pluginPath = os.path.join(mainCodeDirectory, "plugins")

	for root, directories, files in os.walk(mainCodeDirectory):
		if root.startswith(pluginPath) or root.endswith("__pycache__"):
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
	generateUiFiles(uiPath)
	createQtProjectFile(projectPath)
	updateTranslations(projectPath)
	convertImage(iconPath)
	createResourceFile(projectPath, iconPath)
