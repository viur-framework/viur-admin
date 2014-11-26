from zipimport import zipimporter
import imp
import traceback
# Assert that some modules are avaiable to plugins
from PyQt5 import QtGui
import sys, os, os.path


print(sys.argv)
pluginDir = os.path.join(os.getcwd(), "plugins")
if os.path.isdir(pluginDir):
    plugins = os.listdir(pluginDir)

for plugin in plugins:
    if not plugin or plugin.startswith(".") or plugin.endswith("~") or plugin.startswith("_"):
        continue
    if os.path.isdir(os.path.join(pluginDir, plugin)):
        print("Loading Plugin:", plugin)
        file, pathname, descr = imp.find_module(plugin, [pluginDir])
        try:
            imp.load_module(plugin, file, pathname, descr)
        except Exception as e:
            QtGui.QMessageBox.warning(None, "Plugin %s failed to load" % plugin,
                                      "Plugin %s failed to start with: %s\nThis plugin has been disabled and won't be "
                                      "avaiable!" % (
                                      plugin, str(e)))
            print("Error loading Plugin: plugin")
            print(e)
            traceback.print_tb(e.__traceback__)
        finally:
            if file:
                file.close()
    else:
        pluginName = plugin[: plugin.rfind(".")]
        print("Loading Plugin: %s" % pluginName)
        d = zipimporter(os.path.join(pluginDir, plugin))
        d.load_module("plugins.%s" % pluginName)

