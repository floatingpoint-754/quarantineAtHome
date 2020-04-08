#__version__ = "0.0.1.2.3"
__version__ = "1.0.5"

import logging
import os
import sys
import time
import argparse

from pyupdater.client import Client

#import QUARANTINE
#from QUARANTINE.main import PyUpdaterWxDemoApp


# =================== config.py

"""
QUARANTINE/config.py
"""
# We're using UPPERCASE for class attributes but lowerCamelCase
# for instance attributes.  Pylint doesn't distinguish between them:
# pylint: disable=invalid-name

import os
import sys

#import QUARANTINE

from client_config import ClientConfig  # pylint: disable=import-error

CLIENT_CONFIG = ClientConfig()

if 'QUARANTINE_TESTING_APP_NAME' in os.environ:
	CLIENT_CONFIG.APP_NAME = os.environ['QUARANTINE_TESTING_APP_NAME']
if 'QUARANTINE_TESTING_COMPANY_NAME' in os.environ:
	CLIENT_CONFIG.COMPANY_NAME = os.environ['QUARANTINE_TESTING_COMPANY_NAME']
if 'QUARANTINE_TESTING_APP_VERSION' in os.environ:
	__version__ = os.environ['QUARANTINE_TESTING_APP_VERSION']
if 'QUARANTINE_TESTING_PUBLIC_KEY' in os.environ:
	CLIENT_CONFIG.PUBLIC_KEY = os.environ['QUARANTINE_TESTING_PUBLIC_KEY']

def UpdatePyUpdaterClientConfig(clientConfig, port):
	"""
	Update PyUpdater client config.

	This is the configuration (sometimes stored in client_config.py)
	which tells the application where to look for updates.

	The main role of this method to set the UPDATE_URLS in the
	client config.  Because this demo app uses an ephemeral port
	for its file server, the UPDATE_URLS can't be predetermined.

	When called from an automated test, this method if also used
	to set the application's PUBLIC_KEY, which would otherwise be
	generated by "pyupdater keys -c" and stored in client_config.py
	"""
	if clientConfig:
		CLIENT_CONFIG.APP_NAME = clientConfig.APP_NAME
		CLIENT_CONFIG.COMPANY_NAME = clientConfig.COMPANY_NAME
		CLIENT_CONFIG.MAX_DOWNLOAD_RETRIES = clientConfig.MAX_DOWNLOAD_RETRIES
		CLIENT_CONFIG.PUBLIC_KEY = clientConfig.PUBLIC_KEY

	if 'QUARANTINE_DEV' in os.environ:
		print 'devmode! - setting update server to local'
		#updateUrl = 'http://127.0.0.1:%s' % port
		updateUrl = 'http://127.0.0.1:%s' % 1313
		updateUrl = 'http://172.19.0.2:1313/static/clientupdates/'				# docker
		CLIENT_CONFIG.UPDATE_URLS = [updateUrl]



# ------------------- end config.py





# FIXME - find best way to integrate with raven
logger = logging.getLogger(__name__)
STDERR_HANDLER = logging.StreamHandler(sys.stderr)
STDERR_HANDLER.setFormatter(logging.Formatter(logging.BASIC_FORMAT))

class UpdateStatus(object):
	"""Enumerated data type"""
	# pylint: disable=invalid-name
	# pylint: disable=too-few-public-methods
	UNKNOWN = 0
	NO_AVAILABLE_UPDATES = 1
	UPDATE_DOWNLOAD_FAILED = 2
	EXTRACTING_UPDATE_AND_RESTARTING = 3
	UPDATE_AVAILABLE_BUT_APP_NOT_FROZEN = 4
	COULDNT_CHECK_FOR_UPDATES = 5

UPDATE_STATUS_STR = \
	['Unknown',
	 'No available updates were found.',
	 'Update download failed.', 'Extracting update and restarting.',
	 'Update available but application is not frozen.',
	 'Couldn\'t check for updates.']

def ParseArgs(argv):
	"""
	Parse command-line args.
	"""
	usage = ("%(prog)s [options]\n"
			 "\n"
			 "You can also run: python setup.py nosetests")
	parser = argparse.ArgumentParser(usage=usage)
	parser.add_argument("--debug", help="increase logging verbosity", action="store_true")
	parser.add_argument("--version", action='store_true', help="displays version")
	return parser.parse_args(argv[1:])


def InitializeLogging(debug=False):
	"""
	Initialize logging.
	"""
	logger.addHandler(STDERR_HANDLER)
	if debug or 'QUARANTINE_TESTING' in os.environ:
		level = logging.DEBUG
	else:
		level = logging.INFO
	logger.setLevel(level)
	#logging.getLogger("QUARANTINE.fileserver").addHandler(STDERR_HANDLER)			# FIXME - will eventually integrate flask as a more robust fileserver
	#logging.getLogger("QUARANTINE.fileserver").setLevel(level)
	logging.getLogger("pyupdater").setLevel(level)
	logging.getLogger("pyupdater").addHandler(STDERR_HANDLER)


def CheckForUpdates(debug, raven=None):
	"""
	Check for updates.

	Channel options are stable, beta & alpha
	Patches are only created & applied on the stable channel
	"""
	assert CLIENT_CONFIG.PUBLIC_KEY is not None
	client = Client(CLIENT_CONFIG, refresh=True)
	appUpdate = client.update_check(CLIENT_CONFIG.APP_NAME, __version__, channel='stable')

	if appUpdate:
		if hasattr(sys, "frozen"):
			downloaded = appUpdate.download()
			if downloaded:
				status = UpdateStatus.EXTRACTING_UPDATE_AND_RESTARTING

				if 'QUARANTINE_TESTING_FROZEN' in os.environ:
					sys.stderr.write("Exiting with status: %s\n" % UPDATE_STATUS_STR[status])
					#ShutDownFileServer(fileServerPort)
					sys.exit(0)

				#ShutDownFileServer(fileServerPort)
				if debug:
					logger.debug('Extracting update and restarting...')
					time.sleep(10)

				if raven: raven.captureMessage(__version__ + ' Extracting update and restarting')

				appUpdate.extract_restart()
			else:
				status = UpdateStatus.UPDATE_DOWNLOAD_FAILED
				if raven: raven.captureMessage(__version__ + ' Download failed')
		else:
			status = UpdateStatus.UPDATE_AVAILABLE_BUT_APP_NOT_FROZEN
	else:
		status = UpdateStatus.NO_AVAILABLE_UPDATES
	return status


def DisplayVersionAndExit():
	"""
	Display version and exit.

	In some versions of PyInstaller, sys.exit can result in a
	misleading 'Failed to execute script run' message which
	can be ignored: http://tinyurl.com/hddpnft
	"""
	sys.stdout.write("%s\n" % __version__)
	sys.exit(0)


def doUpdate(raven=None):
	debug=True
	InitializeLogging(debug)
	# FIXME - catch failures of this with sentry/raven, but continue allowing the app to run if updates fail
	status = CheckForUpdates(debug, raven=raven)
	sys.stderr.write("Exiting with status: %s\n" % UPDATE_STATUS_STR[status])


def Run(argv, clientConfig=None):
	"""
	The main entry point.
	"""
	args = ParseArgs(argv)
	if args.version:
		DisplayVersionAndExit()

	InitializeLogging(args.debug)
	#fileServerDir = os.environ.get('PYUPDATER_FILESERVER_DIR')
	#fileServerPort = StartFileServer(fileServerDir)

	# dynamically change update server on startup - might re-enable later
	#if fileServerPort:
	#	UpdatePyUpdaterClientConfig(clientConfig, fileServerPort)

	status = CheckForUpdates(args.debug, fileServerPort=None)

	#else:
	#	status = UpdateStatus.COULDNT_CHECK_FOR_UPDATES


	if 'QUARANTINE_TESTING_FROZEN' in os.environ:
		sys.stderr.write("Exiting with status: %s\n" % UPDATE_STATUS_STR[status])
		#ShutDownFileServer(fileServerPort)
		sys.exit(0)

	#mainLoop = (argv[0] != 'RunTester')
	#if not 'QUARANTINE_TESTING_FROZEN' in os.environ:
	#	return PyUpdaterWxDemoApp.Run( fileServerPort, UPDATE_STATUS_STR[status], mainLoop)
	#else:
	#	return None

if __name__ == "__main__":
	#Run(sys.argv)

	doUpdate()

