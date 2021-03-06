from collections import namedtuple
import math
from ROOT import *

RatingMethod = namedtuple("RatingMethod", "name title calc compare")

###############################

def calcSig(sig_nEvents, bkg_nEvents, bkgUnc=None):
	if bkg_nEvents != 0:
		if bkgUnc:
			#print "Significance is calculated using some flat background uncertainty",bkgUnc
			return (sig_nEvents / math.sqrt(bkg_nEvents + (bkgUnc*bkg_nEvents)))
		return (sig_nEvents / math.sqrt(bkg_nEvents))
	else:
		return 0

def compSig(sigA, sigB):
	return sigA > sigB

###############################

def calcOverlap(sigHist, bkgHist, bkgUnc=None):
	# this value should be one when both distributions are identical
	# this value should be zero if both distributions do not overlap
	envelope = sigHist.Clone()
	for ibin in xrange(envelope.GetNbinsX()):
		if envelope.GetBinContent(ibin) < bkgHist.GetBinContent(ibin):
			envelope.SetBinContent(ibin, bkgHist.GetBinContent(ibin))
			# if some error calculation is needed, change also the bin error

	integral = envelope.Integral()
	# if both distributions do not overlap, the integral is two
	# if both distributions are completly identical, the integral is one
	# (both signal and bkg are normalised to unity)
	return (2. - integral)

def compOverlap(areaA, areaB):
	return areaA < areaB

###############################

def calcRooStats(sig_nEvents, bkg_nEvents, bkgUnc=0.2):
	return RooStats.NumberCountingUtils.BinomialExpZ(sig_nEvents, bkg_nEvents, bkgUnc)

def compareRooStats(sigA, sigB):
	return sigA > sigB

###############################

METHODS = [
	RatingMethod("sig", "significane", calcSig, compSig),
	RatingMethod("roostats", "roostats", calcRooStats, compareRooStats)
]

METHODS_RANK = [
	RatingMethod("ovlap", "overlap", calcOverlap, compOverlap)
]


###############################

def getMethod(name, usedList):
	for m in usedList:
		if m.name == name:
			return m
	raise Exception("Method '%s' not found" % name)
