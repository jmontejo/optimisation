#!/usr/bin/env python
import sys
import os

from ROOT import *
import PlotStyle

from tabulate import tabulate
from ratingMethods import *
import getOptimalCut
import utils

###############################

def scale(hist):
	if hist.Integral() != 0:
		hist.Scale(1. / hist.Integral())
	return hist.Clone()

###############################

def getRating(opts, signal, backgrounds):
	sigHist = utils.getHistogram(opts, signal, "sig")
	bkgHist = None
	for i, bkgTree in enumerate(backgrounds):
		if not bkgHist:
			bkgHist = utils.getHistogram(opts, bkgTree, "bkg_" + str(i))
		else:
			bkgHist.Add(utils.getHistogram(opts, bkgTree, "bkg_" + str(i)))

	sigHist = scale(sigHist)
	bkgHist = scale(bkgHist)
	
	rating = opts.method.calc(sigHist, bkgHist)

	storeVar = True
	if opts.method.title == "overlap":
		storeVar = False
		# to avoid problems using the overlap method
		# overlap sometimes wants to cut at the same variable as in the step before
		# this stops the optimisation

	return rating, storeVar, sigHist, bkgHist

###############################

Rating = namedtuple("Rating", "var cut rating lower_cut sigHist bkgHist")

def rankVariables(opts, signal, backgrounds, useGetOptimalCut, bkgUnc, lastCutVar=None):
	gROOT.SetBatch(True)
	varRating = []

	for var, rangeDef in opts.Variables.iteritems():
		cut = None
		rating = None
		storeVar = True
		sigHist = None
		bkgHist = None
		config = getOptimalCut.Settings(opts.method, var, rangeDef.nBins, rangeDef.min, rangeDef.max, opts.event_weight, opts.lumi, opts.enable_plots, opts.preselection, rangeDef.lower_cut)
		if useGetOptimalCut:
			cut, rating, sigHist, bkgHist = getOptimalCut.getOptimalCut(config, signal, backgrounds, bkgUnc)
		else:
			rating, storeVar, sigHist, bkgHist = getRating(config, signal, backgrounds)

		if storeVar:
			varRating.append(Rating(var, cut, rating, rangeDef.lower_cut, sigHist, bkgHist))
			# the variable should generally be stored
		elif (not storeVar) and (var != lastCutVar):
			varRating.append(Rating(var, cut, rating, rangeDef.lower_cut, sigHist, bkgHist))
			# the variable should not be stored for some methods, when it is not used for the ranking
			# e.g. for overlap

	# how to handle other ranking methods, e.g. TMVA methods

	varRating.sort(cmp=lambda a, b: opts.method.compare(a.rating, b.rating) and -1 or 1)

	table = []
	header = None
	if useGetOptimalCut:
		header = ["variable name", "cut value", opts.method.title]
		for rating in varRating:
			table.append([rating.var, rating.cut, rating.rating])
	else:
		header = ["variable name", opts.method.title]
		for rating in varRating:
			table.append([rating.var, rating.rating])
	print tabulate(table, headers=header, tablefmt="simple")

	return varRating

###############################

def parse_options():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument("--enable-plots", action="store_true", help="save all plots")
        parser.add_argument("-p", "--preselection", action="append", default="1", help="preselection for ranges which should not be used for the optimisation (e.g. CR)")
        parser.add_argument("-m", "--method", choices=[m.name for m in METHODS], default="sig", help="which method should be used for the optimisation")
        parser.add_argument("--tree-name", default="CollectionTree", help="tree name for the input file (must be the same for signal and bkg")
        parser.add_argument("--event-weight", default="1.", help="name for the stored event weight")
        parser.add_argument("-l", "--lumi", default=10e3, help="the luminosity which should be used")
        parser.add_argument("-s", "--signal", required=True, help="the signal sample")
        parser.add_argument("-b", "--background", dest="bkgs", required=True, action="append", help="the background sample")
        parser.add_argument("--bkgUnc", default=None, help="the background uncertainty")
     
        parser.add_argument("varFile", help="a python file with a list of variables which should analysed")

        opts = parser.parse_args()

        opts.useGetOptimalCut = False
        for m in METHODS:
        	if opts.method == m.name:
		        opts.method = getMethod(opts.method, METHODS)
		        opts.useGetOptimalCut = True
		for m in METHODS_RANK:
			if opts.method == m.name:
				opts.method = getMethod(opts.method, METHODS_RANK)

        return opts

###############################

def main():
	opts = parse_options()

	sigFile = TFile.Open(opts.signal)
	signal = sigFile.Get(opts.tree_name)

	bkgFileList = []
	backgrounds = []
	for bkg in opts.bkgs:
		bkgFile = TFile.Open(bkg)
		bkgFileList.append(bkgFile)
		backgrounds.append(bkgFile.Get(opts.tree_name))

	config = {}
	execfile(opts.varFile, config)
	variables = config["Variables"]
	opts.Variables = variables

	outcome = rankVariables(opts, signal, backgrounds, useGetOptimalCut, opts.useGetOptimalCut, opts.bkgUnc)

###############################

if __name__ == '__main__':
	main()