import json
import os
import re

import numpy as np
import gzip
import shutil


def compressFile(fileName):
	with open(fileName, 'rb') as f_in:
		gz_ = fileName + '.gz'
		with gzip.open(gz_, 'wb') as f_out:
			shutil.copyfileobj(f_in, f_out)

	return gz_





energyRE = re.compile(r'= {2,3}([-+\d.]*) kcal\/mol')
zincRE = re.compile(r'.*(ZINC[\d]*).*')



class LogParser():
	def __init__(self, fileName):
		self.results = None
		self.poses = []
		self.parse(fileName)

	def parse(self, fileName):
		if fileName.endswith('dlg'):
			with open(fileName) as fh:
				self.parseLines(fh)

		elif fileName.endswith('gz'):
			with gzip.open(fileName) as fh:
				self.parseLines(fh)

	def parseLines(self, fh):

		#firstLine = fh.readline()

		bindingEnergies = []
		ligandAtoms = []

		poses = []
		bindingEnergy = 0

		for line in fh:
			if 'REMARK' in line and 'ZINC' in line:
				# zincID = line.split(' ')[-1].strip()
				zincID = zincRE.findall(line)[0]
				# print line, zincID
				# gonna see some atoms soon!
				ligandAtoms = []
			if 'Estimated Free Energy of Binding' in line:
				# for m in energyRE.findall(line):
				#	print m
				bindingEnergy = float(energyRE.findall(line)[0])

			if line.startswith('DOCKED: ATOM'):  # coordinates!
				ligandAtoms.append(line.replace('DOCKED: ATOM', 'ATOM'))

			if line.startswith('DOCKED: ENDMDL'):
				poses.append(list(ligandAtoms))
				bindingEnergies.append(bindingEnergy)

		energies_poses = zip(bindingEnergies, poses)
		ranked_poses = sorted(energies_poses, key=lambda x: x[0])

		bindingEnergies, poses = zip(*ranked_poses)

		self.poses = poses

		'''
		path, log = os.path.split(fileName)

		for i, pose in enumerate(self.poses):
			poseFile = os.path.join(path, 'pose%s.pdbqt' % i)
			with open(poseFile, 'w') as fh:
				fh.writelines(pose)
		'''


		'''
		if 'AutoDock-GPU' in firstLine:		# GPU version makes slightly different logfiles
				pass
		else:
			for line in fh:
				pass
		'''

		bindingEnergies = np.asarray(bindingEnergies)
		print zincID
		print 'binding energy mean : ', bindingEnergies.mean()
		print 'binding energy min : ', bindingEnergies.min()

		self.results = dict(
			meanDG=bindingEnergies.mean(),
			bestDG=bindingEnergies.min(),
			zincID=zincID
		)


	def savePoses(self, outDir):
		for i, pose in enumerate(self.poses):
			poseFile = os.path.join(outDir, 'pose%s.pdbqt' % (i+1))
			with open(poseFile, 'w') as fh:
				fh.writelines(pose)

	'''
	def saveResults(self, jsonFile):
		with open(jsonFile, 'w') as fh:
			json.dump(self.results, fh)
	'''

	def saveTrajectory(self, trajFile, compress=False):
		def writeLines(fh):
			for i, pose in enumerate(self.poses):
				fh.write('MODEL        %d\n' % (i+1))
				fh.writelines(pose)
				fh.write('ENDMDL\n')

		if compress:
			with gzip.open(trajFile, 'w') as fh: writeLines(fh)
		else:
			with open(trajFile, 'w') as fh: writeLines(fh)


# keep interface the same for now to make merging easier later
def parseLogfile(fileName):
	p = LogParser(fileName)
	return p.results


"""
def parseLogfile(fileName):

	with open(fileName) as fh:
		firstLine = fh.readline()

		bindingEnergies = []

		poses = []
		ligandAtoms = []

		for line in fh:
			if 'REMARK' in line and 'ZINC' in line:
				#zincID = line.split(' ')[-1].strip()
				zincID = zincRE.findall(line)[0]
				#print line, zincID
				# gonna see some atoms soon!
				ligandAtoms = []
			if 'Estimated Free Energy of Binding' in line:
				# for m in energyRE.findall(line):
				#	print m
				bindingEnergy = float(energyRE.findall(line)[0])
				bindingEnergies.append(bindingEnergy)


			if line.startswith('DOCKED: ATOM'):	# coordinates!
				ligandAtoms.append(line.replace('DOCKED: ATOM', 'ATOM'))


			if 'ENDMDLDOCKED' in line:
				poses.append(list(ligandAtoms))


		path, log = os.path.split(fileName)
		for i, pose in enumerate(poses):
			poseFile = os.path.join(path, 'pose%s.pdbqt'%i)
			with open(poseFile, 'w') as fh:
				fh.writelines(pose)


		'''
		if 'AutoDock-GPU' in firstLine:		# GPU version makes slightly different logfiles
				pass
		else:
			for line in fh:
				pass
		'''

		bindingEnergies = np.asarray(bindingEnergies)
		print zincID
		print 'binding energy mean : ', bindingEnergies.mean()
		print 'binding energy min : ', bindingEnergies.min()

		results = dict(
			meanDG = bindingEnergies.mean(),
			bestDG = bindingEnergies.min(),
			zincID = zincID
		)


		return results
"""