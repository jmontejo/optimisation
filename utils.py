from ROOT import *
import sys

def sanitise(var):
	# cleanup characters that may confuse root in histogram names
	BAD_CHARS = "()[]{}+-*/&|"

	for ch in BAD_CHARS:
		var = var.replace(ch, "_")

	return var

def getHistogram(var, nBins, minV, maxV, tree, event_weight, extra_weight, name, preselection, lumi, nMCEvents=False):
	draw_cmd = "{var}>>{hist}"
	draw_cmd += "(" + str(nBins) + "," + str(minV) + "," + str(maxV) + ")"

	eventWeight = event_weight
	if nMCEvents:
		eventWeight = 1
	name += "_" + sanitise(var)

	nEvents = tree.Draw(draw_cmd.format(var=var, hist=name), str(eventWeight) + "*" + str(extra_weight) + "*(" + str(preselection) + ")", "e")
	hist = gDirectory.Get(name)

	if not hist:
		print "ERROR: ", var, " histogram could not be loaded correctly --> maybe it is empty?"
		sys.exit(1)

	if not nMCEvents:
		hist.Scale(lumi)

	hist.SetDirectory(gROOT)

	return hist

def load_chain(filenames, treename, print_files=False):
	if type(treename)==str:
		chain = TChain(treename)
		for name in filenames:
			chain.Add(name)
	elif type(treename)==list:
		chain = TChain(treename[0])
		for name,treename in zip(filenames,treename):
			chain.Add(name+"/"+treename)

	if print_files:
		for filename in chain.GetListOfFiles():
			print filename.GetTitle()

	return chain
