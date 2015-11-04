#!/usr/bin/env python
import sys
import os

from ROOT import *
import PlotStyle
from collections import namedtuple

from ratingMethods import *
from rankVariables import VariableRanker
from getOptimalCut import CutFinder
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

def initGraphs(varList):
	graphs = {}
	for var in varList:
		graphs[var] = TGraph()
	graphs["rating"] = TGraph()
	return graphs

def fillGraphs(graphs, varList, counter):
	for varItem in varList:
		graphs[varItem.var].SetPoint(counter, counter, varItem.cut)

	graphs["rating"].SetPoint(counter, counter, varList[0].rating)

def saveGraphs(graphs, rFile):
	directory = rFile.mkdir("iterationPlots")
	for name, graph in graphs.iteritems():
		directory.WriteTObject(graph, name)

###############################

def initObject(target, source, useGetOptimalCut=None):
	for key in target.__dict__.keys():
		# things only needed for the ranking:
		if key == "useGetOptimalCut":  
			setattr(target, key, useGetOptimalCut)
		elif (key == "finder"):
			pass

		# signal and background are stored as sample object for the optimisation
		# but only as chain for the VariableRanker and CutFinder
		elif (key == "signal"):
			setattr(target, key, getattr(source, key).chain)
		elif (key == "signal_scale"):
			setattr(target, key, getattr(source, "signal").weight)
		elif (key == "backgrounds"):
			setattr(target, key, [b.chain for b in source.backgrounds])
		elif (key == "backgrounds_scale"):
			setattr(target, key, [b.weight for b in source.backgrounds])
		else:
			setattr(target, key, getattr(source, key))

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

	ranker = VariableRanker()
	initObject(ranker, config, rankMeth_inMETHODS)
	finder = CutFinder()
	initObject(finder, config)
	ranker.finder = finder

	graphs = initGraphs(config.Variables)

	while True:
		varList = ranker.rankVariables(config.Variables, counter)
		saveHistograms(rFile, varList, counter)
		fillGraphs(graphs, varList, counter)

		bestVar = varList[0].var 
		
		# when the ranking method is not defined in METHODS, the optimal cut need to be calculated separatly
		if rankMeth_inMETHODS: 
			bestCut = varList[0].cut 
			bestRating = varList[0].rating
			cutDirectionString = "<" if varList[0].lower_cut else ">"
			cutDirection = varList[0].lower_cut
		else:
			rangeDef = config.Variables[bestVar]

			result = finder.getOptimalCut(bestVar, rangeDef.nBins, rangeDef.min, rangeDef.max, rangeDef.lower_cut, counter)
			bestCut = result.cutValue
			bestRating = result.rating
			cutDirectionString = "<" if rangeDef.lower_cut else ">"
			cutDirection = rangeDef.lower_cut

		if prevRating != None and terminateLoop(prevRating, bestRating):
			break

		# add the calculated cut to the preselection for the next iteration
		cutString = " && (" + bestVar + cutDirectionString + str(bestCut) + ")"
		config.preselection += cutString
		ranker.preselection = config.preselection
		finder.preselection = config.preselection

		# prepare a list which is used as final result
		cutList = addToCutList(cutList, bestVar, cutDirection, bestCut)
		
		prevRating = bestRating
		counter += 1

	saveGraphs(graphs, rFile)

	return cutList

###############################

def terminateLoop(prev, cur):
	return abs(prev - cur) / abs(prev) < 0.01

###############################

def parse_options():
		import argparse

		parser = argparse.ArgumentParser()
		parser.add_argument("configFile", help="the configuration stored in a python file")

		opts = parser.parse_args()
		return opts

###############################

def main():
	gROOT.SetBatch(True)
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

	print "\n\nCut string which can directly used for other plotting code"
	print config.preselection

	rFile.Close()


###############################

if __name__ == '__main__':
	main()

###############################

