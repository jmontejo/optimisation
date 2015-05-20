#!/usr/bin/env python
import sys
import os

from ROOT import *
import PlotStyle

import utils
from ratingMethods import *

###############################

def ensure_dir(d):
	if not os.path.exists(d):
		os.makedirs(d)

def saveCanv(opts, canv, directory, append=None, rootFile=False):
	name = opts.var
	if append:
		name = name + "_" + append

	ensure_dir(directory)
	canv.SaveAs(os.path.join(directory, name + ".png")) 
	ensure_dir(directory + "/pdf")
	canv.SaveAs(os.path.join(directory, "pdf", name + ".pdf"))
	if rootFile:
		ensure_dir(directory + "/root")
		canv.SaveAs(os.path.join(directory, "root", name + ".root"))

###############################

def plotVarDistribution(opts, sigHist, bkgHistList):
	sigHist.SetLineColor(kRed + 1)
	sigHist.SetLineWidth(3)

	bkgHist = None
	for hist in bkgHistList:
		if not bkgHist:
			bkgHist = hist
		else:
			bkgHist.Add(hist)

	bkgHist.SetLineColor(kBlue + 2)
	bkgHist.SetLineWidth(3)

	leg = TLegend(0.7, 0.7, 0.9, 0.9)
	leg.SetFillColor(kWhite)
	leg.AddEntry(sigHist, "signal", "L")
	leg.AddEntry(bkgHist, "background", "L")

	stack = THStack()
	stack.Add(sigHist, "hist")
	stack.Add(bkgHist, "hist")
	stack.SetTitle(";" + opts.var + "; # events")

	c = TCanvas("plotVar", "", 600, 600)
	c.SetLogy()
	stack.Draw("nostack")
	leg.Draw("same")

	saveCanv(opts, c, "plots")

def plotRating(opts, graph):
	graph.SetLineWidth(3)
	graph.SetTitle(";" + opts.var + ";" + opts.method.title)

	c = TCanvas("plotRating", "", 600, 600)
	graph.Draw("al")

	saveCanv(opts, c, "plots", "rat")

###############################

def calcIntegral(sigHist, bkgHistList, start, end):
	sig_nEvents = sigHist.Integral(start, end)
	bkg_nEvents = 0
	for bkgHist in bkgHistList:
		bkg_nEvents += bkgHist.Integral(start, end)
	return sig_nEvents, bkg_nEvents

def calcCutRating(opts, sigHist, bkgHistList, bkgUnc, ibin):
	sig_nEvents = 0
	bkg_nEvents = 0
	if opts.lower_cut:
		begin = 0
		sig_nEvents, bkg_nEvents = calcIntegral(sigHist, bkgHistList, begin, ibin)
	else:
		end = sigHist.GetNbinsX()+1
		sig_nEvents, bkg_nEvents = calcIntegral(sigHist, bkgHistList, ibin, end)

	# TODO: fix methods which are lumi depened
	return opts.method.calc(sig_nEvents, bkg_nEvents, bkgUnc)


def checkMCStatistics(opts, sigHistMC, bkgHistMCList, ibin):
	sig_nMCEvents = 0
	bkg_nMCEvents = 0
	if opts.lower_cut:
		begin = 0
		sig_nMCEvents, bkg_nMCEvents = calcIntegral(sigHistMC, bkgHistMCList, begin, ibin)
	else:
		end = sigHistMC.GetNbinsX()+1
		sig_nMCEvents, bkg_nMCEvents = calcIntegral(sigHistMC, bkgHistMCList, ibin, end)

	if (sig_nMCEvents < 10) or (bkg_nMCEvents < 10):
		return False
	return True

###############################

def getRoundedCutValue(opts, binC, hist):
	value = None
	if opts.lower_cut:
		value = hist.GetBinLowEdge(binC+1)
	else:
		value = hist.GetBinLowEdge(binC)
	if opts.max < 10:
		value = round(value,1)
	elif opts.max < 100:
		value = round(value)
	elif opts.max < 2000:
		value = round(value,-1)
	elif opts.max < 10000:
		value = round(value, -2)
	elif opts.max < 100000:
		value = round(value, -3)
	elif opts.max < 1000000:
		value = round(value, -4)
	return value

def checkRoundingEffects(opts, sigHist, bkgHistList, cutValue, rating, bkgUnc):
	binC = sigHist.GetXaxis().FindBin(cutValue)
	ratingRounded = calcCutRating(opts, sigHist, bkgHistList, bkgUnc, binC)
	if abs(rating - ratingRounded) / rating > 0.1:
		print "ERROR: rounding influences the ratings too much"
		return None
	return ratingRounded

def checkCutValue(opts, optimalCutValue, bestBin):
	if opts.lower_cut:
		if (optimalCutValue < opts.max):
			return optimalCutValue # everythin is fine
		elif (optimalCutValue > opts.max) and (bestBin == opts.nBins):
			return opts.max # the overflow bin is chose, set the cut to something meaningful
		else:
			print "ERROR: cut value to larger, but the corresponding bin is not the overflow bin"
			return optimalCutValue
	else:
		if (optimalCutValue > opts.min):
			return optimalCutValue # everything is fine
		elif (optimalCutValue < opts.min) and (bestBin == 0):
			return opts.min # the underflow bin is chosen, set the cut to something meaningful
		else:
			print "ERROR: cut value is too small, but the corresponding bin is not the underflow bin"
			return optimalCutValue

###############################

def addHists(histList):
	sumHist = None
	for hist in histList:
		if not sumHist:
			sumHist = hist
		else:
			sumHist.Add(sumHist)
	return sumHist

###############################

def getOptimalCut(opts, signal, backgrounds, bkgUnc):
	gROOT.SetBatch(True)
	sigHist = utils.getHistogram(opts, signal, "sig")
	sigHistMC = utils.getHistogram(opts, signal, "sigMC", nMCEvents=True)
	bkgHistList = []
	bkgHistMCList = []
	for i, bkgTree in enumerate(backgrounds):
		bkgHistList.append(utils.getHistogram(opts, bkgTree, "bkg_" + str(i)))
		bkgHistMCList.append(utils.getHistogram(opts, bkgTree, "bkgMC_" + str(i), nMCEvents=True))


	if opts.enable_plots:
		plotVarDistribution(opts, sigHist, bkgHistList)

	bestCut = None
	bestBin = None
	graph = TGraph(opts.nBins)
	for ibin in xrange(opts.nBins):
		rating = calcCutRating(opts, sigHist, bkgHistList, bkgUnc, ibin)
		if opts.lower_cut:
			graph.SetPoint(ibin, sigHist.GetBinLowEdge(ibin+1), rating)
		else:
			graph.SetPoint(ibin, sigHist.GetBinLowEdge(ibin), rating)
		
		if not bestCut or opts.method.compare(rating, bestCut):
			if checkMCStatistics(opts, sigHistMC, bkgHistMCList, ibin):
				bestCut = rating
				bestBin = ibin

	if opts.enable_plots:
		plotRating(opts, graph)

	cutValue = getRoundedCutValue(opts, bestBin, sigHist)
	ratingRounded = False# = checkRoundingEffects(opts, sigHist, bkgHistList, cutValue, bestCut, bkgUnc)

	optimalCutValue = None
	optimalRating = None
	if ratingRounded:
		optimalCutValue = cutValue
		optimalRating = ratingRounded
	elif opts.lower_cut:
		optimalCutValue = sigHist.GetBinLowEdge(bestBin+1)
		optimalRating = bestCut
	else:
		optimalCutValue = sigHist.GetBinLowEdge(bestBin)
		optimalRating = bestCut
	
	# check that if the cut Value is lower than min/larger than max the bin should be under/overflow bin
	# the cut value should be set to min or max value of this variable
	optimalCutValue = checkCutValue(opts, optimalCutValue, bestBin)

	bkgHist = addHists(bkgHistList)

	return optimalCutValue, optimalRating, sigHist, bkgHist

###############################

def parse_options():
		import argparse

		parser = argparse.ArgumentParser()

		parser.add_argument("--enable-plots", action="store_true", help="save all plots")
		parser.add_argument("-p", "--preselection", action="append", default="1", help="preselection for ranges which should not be used for the optimisation (e.g. CR)")
		parser.add_argument("-m", "--method", choices=[m.name for m in METHODS], default="sig", help="which method should be used for the optimisation")
		parser.add_argument("--tree-name", default="CollectionTree", help="tree name for the input file (must be the same for signal and bkg")
		parser.add_argument("--event-weight", default="1.", help="name for the stored event weight")
		parser.add_argument("-s", "--signal", required=True, help="the signal sample")
		parser.add_argument("-b", "--background", dest="bkgs", required=True, action="append", help="the background samples")
		parser.add_argument("--bkgUnc", default=None, help="the background uncertainty")
		parser.add_argument("--nBins", default=100, help="the number of bins which are used to define the optimal cut")
		parser.add_argument("--lower-cut", action="store_true", help="events survive when their value is lower than the cut value")

		parser.add_argument("var", help="the variable name which should be analysed (need to be stored in the trees)")
		parser.add_argument("min", help="the minimum value for the variable")
		parser.add_argument("max", help="the maximum value for the variable")

		opts = parser.parse_args()

		opts.method = getMethod(opts.method, METHODS)

		return opts

###############################

Settings = namedtuple("Settings", "method var nBins min max event_weight enable_plots preselection lower_cut")

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


		config = Settings(opts.method, opts.var, opts.nBins, opts.min, opts.max, opts.event_weight, opts.enable_plots, opts.preselection, opts.lower_cut)
		cutValue, rating, sigHist, bkgHist = getOptimalCut(config, signal, backgrounds, opts.bkgUnc)
		print cutValue, rating

###############################

if __name__ == '__main__':
	main()