import os
import sys
import traceback
from distutils.sysconfig import get_python_lib
from urllib import request

"""
Copyright (c) 2012 Bugsnag

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Adapted for ViUR/Python3: 09.04.2013 T.Steinrücken
"""

from typing import Any, Dict


class Notification(object):
	"""
	A single exception notification to Bugsnag.
	"""
	MAX_STRING_LENGTH = 1024

	NOTIFIER_NAME = "Python Bugsnag Notifier"
	NOTIFIER_URL = "https://github.com/bugsnag/bugsnag-python"

	def __init__(self, type: Any, value: Any, tb: Any, configuration: Any, **options: Dict[str, Any]):
		self.type = type
		self.value = value
		self.tb = tb
		self.options = options
		self.configuration = configuration

	def deliver(self) -> None:
		"""
		Deliver the exception notification to Bugsnag.
		"""
		try:
			if self.configuration["apiKey"] == None:
				print("No API key configured, couldn't notify")
				return

			# Generate the URL
			url = "https://notify.bugsnag.com"

			print("Notifying %s of exception" % url)

			# Generate the payload
			payload = self.__generate_payload(**self.options)
			req = request.Request(url, payload, {'Content-Type': 'application/json'})
			try:
				resp = request.urlopen(req)
				status = resp.getcode()
				if status != 200:
					print("Notification to %s failed, got non-200 response code %d" % status)
			except Exception as e:
				print("Notification to %s failed, %s" % (req.get_full_url(), e))

		except Exception as exc:
			print("Notification to %s failed, %s" % (url, exc))

	def __generate_payload(self, **options: Dict[str, Any]) -> str:
		# Set up the lib root
		lib_root = get_python_lib()
		if lib_root and lib_root[-1] != os.sep:
			lib_root += os.sep

		# Set up the project root
		project_root = os.getcwd()
		if project_root and project_root[-1] != os.sep:
			project_root += os.sep

		trace = traceback.extract_tb(self.tb)
		stacktrace = []
		for line in trace:
			file_name = os.path.abspath(str(line[0]))
			in_project = False
			if lib_root and file_name.startswith(lib_root):
				file_name = file_name[len(lib_root):]
			elif project_root and file_name.startswith(project_root):
				file_name = file_name[len(project_root):]
				in_project = True

			stacktrace.append({
				"file": file_name,
				"lineNumber": int(str(line[1])),
				"method": str(line[2]),
				"inProject": in_project,
			})
		# Fetch the notifier version from the package
		notifier_version = "unknown"

		payload = {
			"apiKey": self.configuration["apiKey"],
			"notifier": {
				"name": self.NOTIFIER_NAME,
				"url": self.NOTIFIER_URL,
				"version": notifier_version,
			},
			"events": [{
				"releaseStage": "development" if os.path.exists(".git") else "production",
				"appVersion": self.configuration["appVersion"],
				"context": "",
				"userId": None,
				"exceptions": [{
					"errorClass": str(self.type),
					"message": str(self.value),
					"stacktrace": stacktrace,
				}],
				"metaData": {
					"request": "",
					"environment": dict(os.environ.items()),
					"session": "",
					"extraData": {"platform": sys.platform,
					              "python": sys.version_info}
				}
			}]
		}
		# JSON-encode and return the payload
		return json.dumps(payload).encode("UTF-8")
