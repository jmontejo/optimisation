#!/usr/bin/env python
import sys
import os

from ROOT import *
import PlotStyle

from tabulate import tabulate
from ratingMethods import *
from getOptimalCut import CutFinder
import utils

###############################

def scale(hist):
	if hist.Integral() != 0:
		hist.Scale(1. / hist.Integral())
	return hist.Clone()

###############################

Rating = namedtuple("Rating", "var cut rating lower_cut sigHist bkgHist nEvents_sig nEvents_bkg")

###############################

def initVariableRanker(ranker, opts, signal, backgrounds):
	ranker.signal = signal
	ranker.backgrounds = backgrounds
	ranker.flatBkgUncertainty = opts.flatBkgUncertainty
	ranker.preselection = opts.preselection
	ranker.event_weight = opts.event_weight
	ranker.lumi = opts.lumi
	ranker.method = opts.method
	ranker.useGetOptimalCut = opts.useGetOptimalCut
	ranker.includeMCstat = opts.includeMCstat

###############################

def initCutFinder(finder, ranker):
	for key in finder.__dict__.keys():
		setattr(finder, key, getattr(ranker, key))

###############################

class VariableRanker(object):
	def __init__(self):
		self.signal = None
		self.signal_scale = 1.0
		self.sigMCboundary = 10.
		self.backgrounds = None
		self.backgrounds_scale = None
		self.bkgsMCboundary = None
		self.flatBkgUncertainty = None
		self.preselection = "1"
		self.event_weight = 1.
		self.lumi = 10e3
		self.method = "sig"
		self.enable_plots = False
		self.useGetOptimalCut = False
		self.finder = None
		self.includeMCstat = False

	def rankVariables(self, variables, iteration=0):
		varRating = []

		for var, rangeDef in variables.iteritems():
			cut = None
			rating = None
			storeVar = True
			nEvents_sig = -1
			nEvents_bkg = -1
			sigHist = None
			bkgHist = None

			if self.useGetOptimalCut:
				result = self.finder.getOptimalCut(var, rangeDef.nBins, rangeDef.min, rangeDef.max, rangeDef.lower_cut, iteration)
				cut = result.cutValue
				rating = result.rating
				nEvents_bkg = result.nEvents_bkg
				nEvents_sig = result.nEvents_sig
				sigHist = result.sigHist
				bkgHist = result.bkgHist
			else:
				rating, storeVar, sigHist, bkgHist = self.getRating(var, rangeDef.nBins, rangeDef.min, rangeDef.max)

			if storeVar:
				varRating.append(Rating(var, cut, rating, rangeDef.lower_cut, sigHist, bkgHist, nEvents_sig, nEvents_bkg))
				# the variable should generally be stored
			elif (not storeVar) and (var != lastCutVar):
				varRating.append(Rating(var, cut, rating, rangeDef.lower_cut, sigHist, bkgHist, nEvents_sig, nEvents_bkg))
				# the variable should not be stored for some methods, when it is not used for the ranking
				# e.g. for overlap

		# how to handle other ranking methods, e.g. TMVA methods

		varRating.sort(cmp=lambda a, b: self.method.compare(a.rating, b.rating) and -1 or 1)

		table = []
		header = None
		if self.useGetOptimalCut:
			header = ["variable name", "cut value", self.method.title, "signal", "background"]
			for rating in varRating:
				table.append([rating.var, rating.cut, rating.rating, rating.nEvents_sig, rating.nEvents_bkg])
		else:
			header = ["variable name", self.method.title]
			for rating in varRating:
				table.append([rating.var, rating.rating])
		print tabulate(table, headers=header, tablefmt="simple")

		return varRating

	def getRating(self, var, nbins, minV, maxV):
		sigHist = utils.getHistogram(var, nbins, minV, maxV, self.signal, self.event_weight, self.signal_scale, "sig", self.preselection, self.lumi)
		bkgHist = None

		# if background scale list is not initialized, just fill it with 1.
		if not self.backgrounds_scale:
			for i in xrange(len(self.backgrounds)):
				self.backgrounds_scale.append(1.0)

		for i, bkgTree in enumerate(self.backgrounds):
			if not bkgHist:
				bkgHist = utils.getHistogram(var, nbins, minV, maxV, bkgTree, self.event_weight, self.backgrounds_scale[i], "bkg_" + str(i), self.preselection, self.lumi)
			else:
				bkgHist.Add(utils.getHistogram(var, nbins, minV, maxV, bkgTree, self.event_weight, self.backgrounds_scale[i], "bkg_" + str(i), self.preselection, self. lumi))

		sigHist = scale(sigHist)
		bkgHist = scale(bkgHist)
		
		rating = self.method.calc(sigHist, bkgHist)

		storeVar = True
		if self.method.title == "overlap":
			storeVar = False
			# to avoid problems using the overlap method
			# overlap sometimes wants to cut at the same variable as in the step before
			# this stops the optimisation

		return rating, storeVar, sigHist, bkgHist

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
        parser.add_argument("--flatBkgUncertainty", default=None, help="the background uncertainty")
        parser.add_argument("--includeMCstat", action="store_true", help="Consider MC statistics in the uncertainty")
     
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
	gROOT.SetBatch(True)
	opts = parse_options()

	signal = utils.load_chain([opts.signal], opts.tree_name, print_files=True)

	backgrounds = []
	for bkg in opts.bkgs:
		backgrounds.append(utils.load_chain([bkg], opts.tree_name, print_files=True))

	ranker = VariableRanker()
	initVariableRanker(ranker, opts, signal, backgrounds)

	finder = CutFinder()
	initCutFinder(finder, self)
	ranker.finder = finder

	config = {}
	execfile(opts.varFile, config)
	variables = config["Variables"]

	outcome = ranker.rankVariables(variables)

###############################

if __name__ == '__main__':
	main()
