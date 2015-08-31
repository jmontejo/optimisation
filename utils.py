from ROOT import *
import sys

def getHistogram(var, nBins, minV, maxV, tree, event_weight, name, preselection, lumi, nMCEvents=False):
	draw_cmd = "{var}>>{hist}"
	draw_cmd += "(" + str(nBins) + "," + str(minV) + "," + str(maxV) + ")"

	eventWeight = event_weight
	if nMCEvents:
		eventWeight = 1
	name += "_" + var

	nEvents = tree.Draw(draw_cmd.format(var=var, hist=name), str(eventWeight) + "*(" + str(preselection) + ")", "e")
	hist = gDirectory.Get(name)

	if not hist:
		print "ERROR: histogram could not be loaded correctly --> maybe it is empty?"
		sys.exit(1)

	if not nMCEvents:
		hist.Scale(lumi)

	hist.SetDirectory(gROOT)

	return hist

def load_chain(filenames, treename, print_files=False):
	chain = TChain(treename)
	for name in filenames:
		chain.Add(name)

	if print_files:
		for filename in chain.GetListOfFiles():
			print filename.GetTitle()

	return chain