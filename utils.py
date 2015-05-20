from ROOT import *
import sys

def getHistogram(opts, sample, name, nMCEvents=False):
	draw_cmd = "{var}>>{hist}"
	draw_cmd += "(" + str(opts.nBins) + "," + str(opts.min) + "," + str(opts.max) + ")"

	eventWeight = opts.event_weight
	if nMCEvents:
		eventWeight = 1
	else:
		eventWeight = "(" + str(eventWeight) + "*" + str(opts.lumi) + ")"
	name += "_" + opts.var
	tree = sample.chain
	nEvents = tree.Draw(draw_cmd.format(var=opts.var, hist=name), str(eventWeight) + "*(" + str(opts.preselection) + ")", "e")
	hist = gDirectory.Get(name)

	if not hist:
		print "ERROR: histogram could not be loaded correctly --> maybe it is empty?"
		sys.exit(1)

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