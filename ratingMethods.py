from collections import namedtuple
import math

RatingMethod = namedtuple("RatingMethod", "name title calc compare")

###############################

def calcSig(sig_nEvents, bkg_nEvents):
	if bkg_nEvents != 0:
		return (sig_nEvents / math.sqrt(bkg_nEvents))
	else:
		return 0

def compSig(sigA, sigB):
	return sigA > sigB

###############################

def calcOverlap(sigHist, bkgHist):
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

METHODS = [
	RatingMethod("sig", "significane", calcSig, compSig)
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