# -*- coding: utf-8 -*-

# import importlib
# import importlib.util
# import os
# import os.path
# from zipimport import zipimporter
#
# from PyQt5 import QtWidgets
#
# from viur_admin import log
#
# logger = log.getLogger(__name__)
#
#
# def loadPlugins():
# 	dirname = os.path.dirname(os.path.realpath(__file__))
#
# 	pluginDir = os.path.join(dirname, "plugins")
# 	if os.path.isdir(pluginDir):
# 		plugins = os.listdir(pluginDir)
#
# 	for plugin in plugins:
# 		if not plugin or plugin.startswith(".") or plugin.endswith("~") or plugin.startswith("_"):
# 			continue
# 		if os.path.isdir(os.path.join(pluginDir, plugin)):
# 			print("loading plugin")
# 			logger.debug("Loading Plugin: %r", plugin)
# 			try:
# 				importlib.import_module("viur_admin.plugins.{pluginName}".format(pluginName=plugin))
# 			except Exception as err:
# 				QtWidgets.QMessageBox.warning(None, "Plugin %s failed to load" % plugin,
# 				                              "Plugin %s failed to start with: %s\nThis plugin has been disabled and won't be "
# 				                              "avaiable!" % (
# 					                              plugin, str(err)))
# 				logger.error("Error loading Plugin: %r", plugin)
# 				logger.exception(err)
# 		else:
# 			pluginName = plugin[: plugin.rfind(".")]
# 			d = zipimporter(os.path.join(pluginDir, plugin))
# 			d.load_module("plugins.%s" % pluginName)

