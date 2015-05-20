#!/usr/bin/env python
import sys
import os

from ROOT import *
import PlotStyle
from collections import namedtuple

from ratingMethods import *
import rankVariables
import getOptimalCut
import configuration
from tabulate import tabulate


###############################

def checkInputSettings(config):
	# check whether the important inputs are set
	if not config.signal:
		print "ERROR: no signal tree is selected"
		sys.exit(1)
	if not config.backgrounds:
		print "ERROR: no background tree is selected"
		sys.exit(1)
	if not config.Variables:
		print "ERROR: no variables are defined which should be used for the optimisation"
		sys.exit(1)

###############################
CutInformation = namedtuple("CutInformation", "value lower_cut")

def addToCutList(cutList, bestVar, lower_cut, cutValue):
	# test whether the cutDirection is the same
	# change the cut value (if it is in the correct direction)
	if bestVar in cutList:
		if cutList[bestVar].lower_cut != lower_cut:
			print "ERROR: the direction of the cut is changed somewhere"
			sys.exit(1)
		if lower_cut and (cutList[bestVar].value < cutValue):
			print "ERROR: the new cut value is bigger than the old one (it should be smaller)"
			sys.exit(1)
		elif (not lower_cut) and (cutList[bestVar].value > cutValue):
			print "ERROR: the new cut value is smaller than the old one (it should be higher)"
			sys.exit(1)
		else:
			cutList[bestVar] = CutInformation(cutValue, lower_cut)

	else:
		cutList[bestVar] = CutInformation(cutValue, lower_cut)

	return cutList

###############################

def saveHistograms(rFile, varList, counter):
	# creates a directory where the different distributions are stored
	directory = rFile.mkdir("step_" + str(counter))

	for var in varList:
		if var.sigHist:
			directory.WriteTObject(var.sigHist, "sig_" + var.var)
		if var.bkgHist:
			directory.WriteTObject(var.bkgHist, "bkg_" + var.var)

###############################

def optimiseCuts(config, rFile):
	rankMeth_inMETHODS = False
	for m in METHODS:
		if config.rankingMethod == m.name:
			config.method = getMethod(config.rankingMethod, METHODS)
			rankMeth_inMETHODS = True
	if not rankMeth_inMETHODS:
		config.method = getMethod(config.rankingMethod, METHODS_RANK)

	optMethod = getMethod(config.optimisationMethod, METHODS)
	prevRating = None
	bestCut = None
	bestRating = None
	cutDirectionString = None
	cutDirection = None
	bestVar = None
	cutList = {}
	counter = 0

	while True:
		varList = rankVariables.rankVariables(config, config.signal, config.backgrounds, rankMeth_inMETHODS, bestVar)
		saveHistograms(rFile, varList, counter)

		bestVar = varList[0].var 
		
		# when the ranking method is not defined in METHODS, the optimal cut need to be calculated separatly
		if rankMeth_inMETHODS: 
			bestCut = varList[0].cut 
			bestRating = varList[0].rating
			cutDirectionString = "<" if varList[0].lower_cut else ">"
			cutDirection = varList[0].lower_cut
		else:
			rangeDef = config.Variables[bestVar]
			optiConfig = getOptimalCut.Settings(optMethod, bestVar, rangeDef.nBins, rangeDef.min, rangeDef.max, config.event_weight, config.enable_plots, config.preselection, rangeDef.lower_cut)
			bestCut, bestRating, sigHist, bkgHist = getOptimalCut.getOptimalCut(optiConfig, config.signal, config.backgrounds)
			cutDirectionString = "<" if rangeDef.lower_cut else ">"
			cutDirection = rangeDef.lower_cut

		if prevRating != None and terminateLoop(prevRating, bestRating):
			break

		# add the calculated cut to the preselection for the next iteration
		cutString = "*(" + bestVar + cutDirectionString + str(bestCut) + ")"
		config.preselection += cutString

		# prepare a list which is used as final result
		cutList = addToCutList(cutList, bestVar, cutDirection, bestCut)
		
		prevRating = bestRating
		counter += 1

	return cutList

###############################

def terminateLoop(prev, cur):
	return abs(prev - cur) / prev < 0.01

###############################

def parse_options():
		import argparse

		parser = argparse.ArgumentParser()
		parser.add_argument("configFile", help="the configuration stored in a python file")

		opts = parser.parse_args()
		return opts

###############################

def main():
	gROOT.ProcessLine("gErrorIgnoreLevel = 1001;") # ignore INFO and below

	opts = parse_options()

	config = configuration.load_config(opts.configFile)

	rFile = TFile(opts.configFile.replace(".py", ".root"), "RECREATE")

	checkInputSettings(config)
	cutList = optimiseCuts(config, rFile)


	table = []
	print "\n\nFINAL RESULTS\n"
	header = ["variable name", "cut direction", "cut value"]
	for cut, cutInfo in cutList.iteritems():
		cutDirectionString = "<" if cutInfo.lower_cut else ">"
		table.append([cut, cutDirectionString, cutInfo.value])
	print tabulate(table, headers=header, tablefmt="simple")

	rFile.Close()


###############################

if __name__ == '__main__':
	main()