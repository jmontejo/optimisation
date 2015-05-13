from ROOT import *
OBJECTS = []

def getHistogram(opts, tree, name, nMCEvents=False):
	draw_cmd = "{var}>>{hist}"
	draw_cmd += "(" + str(opts.nBins) + "," + str(opts.min) + "," + str(opts.max) + ")"

	eventWeight = opts.event_weight
	if nMCEvents:
		eventWeight = 1
	name += "_" + opts.var
	nEvents = tree.Draw(draw_cmd.format(var=opts.var, hist=name), str(eventWeight) + "*(" + str(opts.preselection) + ")", "e")
	hist = gDirectory.Get(name)

	if not hist:
		print "ERROR: histogram could not be loaded correctly --> maybe it is empty?"
		sys.exit(1)

	hist.SetDirectory(gROOT)

	return hist

def load_tree(filenames, treename):
	treeList = []
	for name in filenames:
		f = TFile.Open(name)
		OBJECTS.append(f)
		treeList.append(f.Get(treename))
	return treeList
