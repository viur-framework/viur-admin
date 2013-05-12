import os
from zipimport import zipimporter
import imp
import traceback
#Assert that some modules are avaiable to plugins
from PySide import QtCore, QtGui, QtOpenGL
import base64, sys, os, os.path, hashlib, datetime, heapq, queue, weakref, types, copy, pprint, math
import random, tempfile, shutil, json, zlib, gzip, bz2, zipfile, tarfile, csv, io, time, threading, mmap
import socket, ssl, signal, asyncore, asynchat, email, mimetypes, binhex, binascii, uu
import html, html.parser, html.entities, xml.dom, xml.dom.minidom, xml.dom.pulldom, socketserver
import urllib, urllib.request, urllib.response, urllib.error, urllib.robotparser, poplib, imaplib, smtplib, nntplib


print (sys.argv)
pluginDir = os.path.join(os.getcwd(), "plugins")
if os.path.isdir( pluginDir ):
	plugins = os.listdir( pluginDir )

for plugin in plugins:
	if not plugin or plugin.startswith(".") or plugin.endswith("~") or plugin.startswith("_"):
		continue
	if os.path.isdir( os.path.join( pluginDir, plugin ) ):
		print( "Loading Plugin:", plugin)
		file, pathname, descr = imp.find_module( plugin, [pluginDir] )
		try:
			imp.load_module(plugin, file, pathname, descr)
		except Exception as e:
			print("Error loading Plugin: plugin")
			print( e )
			traceback.print_tb( e.__traceback__)
		finally:
			if file:
				file.close()			
	else:
		pluginName = plugin[ : plugin.rfind(".") ]
		print( "Loading Plugin: %s" % pluginName )
		d = zipimporter( os.path.join(pluginDir, plugin) )
		d.load_module("plugins.%s" % pluginName)

