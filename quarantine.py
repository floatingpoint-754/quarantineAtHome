from updates import doUpdate, __version__
doUpdate()
import sys
print 'Current version is : ', __version__
#sys.exit(1)



import argparse
import json
import logging
import os
import sys
import time
from random import shuffle

from docking.autodock import runAutodock
from docking.autogrid import runAutogrid
from docking.parsers import LogParser
from getjob import API, TrancheReader
from settings import LOCAL_RESULTS_DIR, getwd
from util import Receptor
from webgui import GUIServer

parser = argparse.ArgumentParser()
parser.parse_args()

from raven import Client

client = Client('https://95200bce44ef41ae828324e243dc3240:4d2b75ff840d434490a507511340c7f7@bugs.infino.me/6')
sentry_errors_log = logging.getLogger("sentry.errors")
sentry_errors_log.addHandler(logging.StreamHandler())

#print os.getcwd()
#print getwd()
#sys.exit(0)


#!/usr/bin/env python
import signal
import sys

def signal_handler(sig, frame):
	print('You pressed Ctrl+C!')
	sys.exit(13)
signal.signal(signal.SIGINT, signal_handler)
print('Press Ctrl+C')
#signal.pause()

'''
try:
	1 / 0
except ZeroDivisionError:
	client.captureException()
'''


'''
The primary loop for the client ....

To minimize bandwidth requirements on the UCSF Zinc database, clients will download single tranche files,
and generally stick with them for lengthy periods of time. Thus, the outer loop is a request to the server of 
which tranche file should be processed.
'''


devmode = os.getenv('DEBUG')		# if set, enters developer mode (contacts local server
USERNAME = os.getenv('ME')		# if set, enters developer mode (contacts local server



# make the GUI server and open a browser



def jobLoop():
	client = API(USERNAME, dev=devmode)

	gui = GUIServer()
	gui.startServer().openBrowser()

	while True:

		trancheID, tranche = client.nextTranche()		# contact server for a tranche assignment
		TR = TrancheReader(trancheID, tranche, mirror=client.mirror)			# then download and open this tranche for reading

		# inner loop - which ligand models from this tranche file should we execute?
		while True:
			# get model number from server
			ligandNum, receptors = client.nextLigand(trancheID)					# ask server which ligand model number to execute
			print 'Server told us to work on model ', ligandNum

			try: zincID, model = TR.getModel(ligandNum)					# parse out of Tranche file
			except StopIteration:
				client.trancheEOF(trancheID)
				break

			# these are saved so the frontend displays info on the active ligand
			#TR.saveModel(model, outfile=os.path.join(LOCAL_RESULTS_DIR, 'ligand.pdbqt'))
			TR.saveModel(model, outfile=os.path.join(getwd(), 'ligand.pdbqt'))
			#gui.ligand = zincID

			for receptorName in receptors:

				receptor = Receptor(receptorName)

				workDir = receptor.dir          # sloppy, will change later

				gui.nextJob(zincID, receptor.name)

				TR.saveModel(model, outfile=os.path.join(workDir, 'ligand.pdbqt'))					# job directory

				start = time.time()
				gui.appendToLog('Starting Autogrid')
				runAutogrid(cwd=workDir)
				#results, logFile = runAutodock(cwd=dir)

				gui.appendToLog('Starting Autodock')
				#gui.tailLog( os.path.join(workDir, 'docking.dlg') )        # not working right
				algo, logFile = runAutodock(cwd=workDir)

				PR = LogParser(logFile)
				results = PR.results
				results['algo'] = algo
				end = time.time()
				results['time'] = end-start
				results['receptor'] = receptor.name
				results['tranche'] = trancheID
				results['ligand'] = ligandNum

				jobID = client.reportResults(results, logFile, username=gui.settings.username)

				#### Save local results for the client interface

				# FIXME - store all results to disk so user can browse them locally
				# FIXME - I'll do this later - not important for prototype
				#localResults = os.path.join(LOCAL_RESULTS_DIR, receptor.name)
				#if not os.path.exists(localResults): os.makedirs(localResults)

				localResults = getwd()
				PR.saveTrajectory( os.path.join(localResults, 'lastTrajectory.pdbqt') )
				gui.jobFinished(jobID, results)


if __name__ == '__main__':
	jobLoop()



