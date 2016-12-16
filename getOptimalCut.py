#!/usr/bin/env python
import sys
import os
from math import *

from ROOT import *
import PlotStyle

import utils
from ratingMethods import *

###############################

def ensure_dir(d):
	if not os.path.exists(d):
		os.makedirs(d)

def saveCanv(var, canv, directory, append=None, rootFile=False):
	name = var
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

def plotVarDistribution(var, sigHist, bkgHistList):
	sigHist.SetLineColor(kRed + 1)
	sigHist.SetLineWidth(3)

	bkgHist = None
	for hist in bkgHistList:
		if not bkgHist:
			bkgHist = hist.Clone()
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
	stack.SetTitle(";" + var + "; # events")

	c = TCanvas("plotVar", "", 600, 600)
	c.SetLogy()
	stack.Draw("nostack")
	leg.Draw("same")

	saveCanv(var, c, "plots")

def plotRating(var, title, graph):
	graph.SetLineWidth(3)
	graph.SetTitle(";" + var + ";" + title)

	c = TCanvas("plotRating", "", 600, 600)
	graph.Draw("al")

	saveCanv(var, c, "plots", "rat")

###############################

def calcIntegral(sigHist, bkgHistList, start, end):
	sig_nEvents = sigHist.Integral(start, end)
	bkg_nEvents = 0
	for bkgHist in bkgHistList:
		bkg_nEvents += bkgHist.Integral(start, end)
	return sig_nEvents, bkg_nEvents

def calcSingleIntegrals(sigHist, bkgHistList, start, end):
	sig_nEvents = sigHist.Integral(start, end)
	bkg_nEventsList = []
	for bkgHist in bkgHistList:
		bkg_nEventsList.append(bkgHist.Integral(start, end))
	return sig_nEvents, bkg_nEventsList

def calcBkgIntegrals(bkgHistList, start, end):
	bkg_nEventsList = []
	for bkgHist in bkgHistList:
		bkg_nEventsList.append(bkgHist.Integral(start, end))
	return bkg_nEventsList

def calcIntegralError(sigHist, bkgHistList, start, end):
	sig_error = Double()
	bkg_error = Double()
	totbkg_error = 0
	sig_nEvents = sigHist.IntegralAndError(start, end,sig_error)
	bkg_nEvents = 0
	for bkgHist in bkgHistList:
		bkg_nEvents += bkgHist.IntegralAndError(start, end, bkg_error)
		totbkg_error += bkg_error*bkg_error
	totbkg_error = sqrt(totbkg_error)
	if sig_nEvents==0 or bkg_nEvents==0:
		return 1,1
	return sig_error/sig_nEvents, totbkg_error/bkg_nEvents

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

def initCutFinder(finder, opts, signal, backgrounds):
	finder.signal = signal
	finder.backgrounds = backgrounds
	finder.flatBkgUncertainty = opts.flatBkgUncertainty
	finder.preselection = opts.preselection
	finder.event_weight = opts.event_weight
	finder.lumi = opts.lumi
	finder.method = opts.method
	finder.includeMCstat = opts.includeMCstat

###############################

CutResult = namedtuple("CutResult", "cutValue rating sigHist bkgHist nEvents_sig nEvents_bkg")

###############################

class CutFinder(object):
	def __init__(self):
		self.signal = None
		self.signal_scale = 1.
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
		self.damp_func = None
		self.includeMCstat = False

	def getOptimalCut(self, var, nbins, minV, maxV, lower_cut, iteration=0):
		sigHist = utils.getHistogram(var, nbins, minV, maxV, self.signal, self.event_weight, self.signal_scale, "sig", self.preselection, self.lumi)
		sigHistMC = utils.getHistogram(var, nbins, minV, maxV, self.signal, self.event_weight, self.signal_scale, "sigMC", self.preselection, self.lumi, nMCEvents=True)
		bkgHistList = []
		bkgHistMCList = []

		# if background scale list is not initialized, just fill it with 1.
		if not self.backgrounds_scale:
			for i in xrange(len(self.backgrounds)):
				self.backgrounds_scale.append(1.0)

		for i, bkgTree in enumerate(self.backgrounds):
			bkgHistList.append(utils.getHistogram(var, nbins, minV, maxV, bkgTree, self.event_weight, self.backgrounds_scale[i], "bkg_" + str(i), self.preselection, self.lumi))
			bkgHistMCList.append(utils.getHistogram(var, nbins, minV, maxV, bkgTree, self.event_weight, self.backgrounds_scale[i], "bkgMC_" + str(i), self.preselection, self.lumi, nMCEvents=True))


		if self.enable_plots:
			plotVarDistribution(var, sigHist, bkgHistList)

		bestCut = None
		bestBin = None
		nEvents_sig = -1
		nEvents_bkg = -1
		graph = TGraph()
		for ibin in xrange(nbins):
			rating = self.calcCutRating(sigHist, bkgHistList, lower_cut, ibin)
			if lower_cut:
				graph.SetPoint(ibin, sigHist.GetBinLowEdge(ibin+1), rating)
			else:
				graph.SetPoint(ibin, sigHist.GetBinLowEdge(ibin), rating)
			
			if not bestCut or self.method.compare(rating, bestCut):
				if not self.bkgsMCboundary:
					for i in xrange(len(self.backgrounds)):
						self.bkgsMCboundary.append(10.)
				if (self.checkMCStatistics(sigHistMC, bkgHistMCList, self.sigMCboundary, self.bkgsMCboundary, lower_cut, ibin) and self.doDamping(bkgHistList, lower_cut, ibin, iteration)):
					bestCut = rating
					bestBin = ibin
					if lower_cut:
						nEvents_sig, nEvents_bkg = calcIntegral(sigHist, bkgHistList, 0, ibin)
					else:
						nEvents_sig, nEvents_bkg = calcIntegral(sigHist, bkgHistList, ibin, sigHist.GetNbinsX()+1)
					
		if self.enable_plots:
			plotRating(var, self.method.title, graph)

		if not bestBin:
			bestBin = 0
		cutValue = self.getRoundedCutValue(bestBin, sigHist, maxV, lower_cut)
		ratingRounded = False# = self.checkRoundingEffects(opts, sigHist, bkgHistList, cutValue, bestCut, lower_cut)

		optimalCutValue = None
		optimalRating = None
		if ratingRounded:
			optimalCutValue = cutValue
			optimalRating = ratingRounded
		elif lower_cut:
			optimalCutValue = sigHist.GetBinLowEdge(bestBin+1)
			optimalRating = bestCut
		else:
			optimalCutValue = sigHist.GetBinLowEdge(bestBin)
			optimalRating = bestCut
		
		# check that if the cut Value is lower than min/larger than max the bin should be under/overflow bin
		# the cut value should be set to min or max value of this variable
		optimalCutValue = self.checkCutValue(optimalCutValue, bestBin, nbins, minV, maxV, lower_cut)

		bkgHist = addHists(bkgHistList)
		return CutResult(optimalCutValue, optimalRating, sigHistMC, bkgHist, nEvents_sig, nEvents_bkg)

	def calcCutRating(self, sigHist, bkgHistList, lower_cut, ibin):
		sig_nEvents = 0
		bkg_nEvents = 0
		if lower_cut:
			begin = 0
			sig_nEvents,  bkg_nEvents  = calcIntegral(sigHist, bkgHistList, begin, ibin)
			sig_relerror, bkg_relerror = calcIntegralError(sigHist, bkgHistList, begin, ibin)
		else:
			end = sigHist.GetNbinsX()+1
			sig_nEvents,  bkg_nEvents  = calcIntegral(sigHist, bkgHistList, ibin, end)
			sig_relerror, bkg_relerror = calcIntegralError(sigHist, bkgHistList, ibin, end)

		# TODO: fix methods which are lumi depened
		uncertainty = self.flatBkgUncertainty
		if self.includeMCstat:
			uncertainty = sqrt(pow(self.flatBkgUncertainty,2)+pow(sig_relerror,2)+pow(bkg_relerror,2))
		return self.method.calc(sig_nEvents, bkg_nEvents, uncertainty)

	def doDamping(self, bkgHistList, lower_cut, ibin, iteration):
		if not self.damp_func:
			return True
		bkg_nEventsList = []

		begin = 0
		end = bkgHistList[0].GetNbinsX()+1
		if lower_cut:
			bkg_nEventsList = calcBkgIntegrals(bkgHistList, begin, ibin)
		else:
			bkg_nEventsList = calcBkgIntegrals(bkgHistList, ibin, end)

		totalBkgEventsList = calcBkgIntegrals(bkgHistList, begin, end)

		#print iteration, self.damp_func(iteration), bkg_nEventsList[0], totalBkgEventsList[0]
		for i in xrange(len(bkg_nEventsList)):
			if bkg_nEventsList[i] < (self.damp_func(iteration) * totalBkgEventsList[i]):
				return False
		return True


	# same function for exp events depending on damping
	def checkMCStatistics(self, sigHistMC, bkgHistMCList, sigMCboundary, bkgsMCboundary, lower_cut, ibin):
		sig_nMCEvents = 0
		bkg_nMCEventsList = []
		if lower_cut:
			begin = 0
			sig_nMCEvents, bkg_nMCEventsList = calcSingleIntegrals(sigHistMC, bkgHistMCList, begin, ibin)
		else:
			end = sigHistMC.GetNbinsX()+1
			sig_nMCEvents, bkg_nMCEventsList = calcSingleIntegrals(sigHistMC, bkgHistMCList, ibin, end)

		if (sig_nMCEvents < sigMCboundary):
			# bkg_Events < returnDamp * totalBkgEvents
			return False
		for i in xrange(len(bkg_nMCEventsList)):
			if bkg_nMCEventsList[i] < bkgsMCboundary[i]:
				return False
		return True

	def getRoundedCutValue(self, binC, hist, maxV, lower_cut):
		value = None
		if lower_cut:
			value = hist.GetBinLowEdge(binC+1)
		else:
			value = hist.GetBinLowEdge(binC)
		if maxV < 10:
			value = round(value,1)
		elif maxV < 100:
			value = round(value)
		elif maxV < 2000:
			value = round(value,-1)
		elif maxV < 10000:
			value = round(value, -2)
		elif maxV < 100000:
			value = round(value, -3)
		elif maxV < 1000000:
			value = round(value, -4)
		return value

	def checkRoundingEffects(self, sigHist, bkgHistList, cutValue, rating, lower_cut):
		binC = sigHist.GetXaxis().FindBin(cutValue)
		ratingRounded = self.calcCutRating(sigHist, bkgHistList, lower_cut, binC)
		if abs(rating - ratingRounded) / rating > 0.1:
			print "ERROR: rounding influences the ratings too much"
			return None
		return ratingRounded

	def checkCutValue(self, optimalCutValue, bestBin, nbins, minV, maxV, lower_cut):
		if lower_cut:
			if (optimalCutValue < maxV):
				return optimalCutValue # everythin is fine
			elif (optimalCutValue > maxV) and (bestBin == nbins):
				return maxV # the overflow bin is chose, set the cut to something meaningful
			else:
				print "ERROR: cut value to larger, but the corresponding bin is not the overflow bin"
				return optimalCutValue
		else:
			if (optimalCutValue > minV):
				return optimalCutValue # everything is fine
			elif (optimalCutValue < minV) and (bestBin == 0):
				return minV # the underflow bin is chosen, set the cut to something meaningful
			else:
				print "ERROR: cut value is too small, but the corresponding bin is not the underflow bin"
				return optimalCutValue


###############################

def parse_options():
		import argparse

		parser = argparse.ArgumentParser()

		parser.add_argument("--enable-plots", action="store_true", help="save all plots")
		parser.add_argument("-p", "--preselection", action="append", default="1", help="preselection for ranges which should not be used for the optimisation (e.g. CR)")
		parser.add_argument("-m", "--method", choices=[m.name for m in METHODS], default="sig", help="which method should be used for the optimisation")
		parser.add_argument("--tree-name", default="CollectionTree", help="tree name for the input file (must be the same for signal and bkg")
		parser.add_argument("--event-weight", default="1.", help="name for the stored event weight")
		parser.add_argument("-l", "--lumi", default=10e3, help="the luminosity which should be used for the optimisation")
		parser.add_argument("-s", "--signal", required=True, help="the signal sample")
		parser.add_argument("-b", "--background", dest="bkgs", required=True, action="append", help="the background samples")
		parser.add_argument("--flatBkgUncertainty", default=None, help="the background uncertainty")
		parser.add_argument("--nbins", default=100, help="the number of bins which are used to define the optimal cut")
		parser.add_argument("--lower-cut", action="store_true", help="events survive when their value is lower than the cut value")
		parser.add_argument("--includeMCstat", action="store_true", help="Consider MC statistics in the uncertainty")

		parser.add_argument("var", help="the variable name which should be analysed (need to be stored in the trees)")
		parser.add_argument("min", type=float, help="the minimum value for the variable")
		parser.add_argument("max", type=float, help="the maximum value for the variable")

		opts = parser.parse_args()

		opts.method = getMethod(opts.method, METHODS)

		return opts

###############################

def main():
	gROOT.SetBatch(True)
	opts = parse_options()

	signal = utils.load_chain([opts.signal], opts.tree_name, print_files=True)

	backgrounds = []
	for bkg in opts.bkgs:
		backgrounds.append(utils.load_chain([bkg], opts.tree_name, print_files=True))

	finder = CutFinder()
	initCutFinder(finder, opts, signal, backgrounds)

	result = finder.getOptimalCut(opts.var, opts.nbins, opts.min, opts.max, opts.lower_cut)
	print result.cutValue, result.rating

###############################

if __name__ == '__main__':
	main()
