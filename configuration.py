import ROOT
from collections import namedtuple
Sample = namedtuple("Sample", "name chain weight color")

class Configuration(object):
	def __init__(self):
		self.signal = None
		self.backgrounds = None
		self.Variables = None
		self.preselection = "1"
		self.event_weight = 1.
		self.add_weight = None
		self.lumi = 10e3
		self.enable_plots = False
		self.rankingMethod = "sig"
		self.optimisationMethod = "sig"
		self.flatBkgUncertainty = None
		self.method = None
		self.use_validation = False # if enabled, an output tree is produced

def sample(name, chain, weight=1.0, color=ROOT.kBlack):
	return Sample(name, chain, weight, color)

def load_config(filename):
	import utils

	Range = namedtuple("Range", "min max nBins lower_cut")

	config = Configuration()

	env = {
		"Config": config, 
		"Utils": utils, 
		'ROOT': ROOT,
		'Range': Range,
		'Sample': sample,
	}

	execfile(filename, env)

	return config
