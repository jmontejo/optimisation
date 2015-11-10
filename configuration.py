import ROOT
from collections import namedtuple
Sample = namedtuple("Sample", "name chain weight color MCboundary")

def damp_linear5(iterations):
	if iterations >= 5:
		return 0.
	return 0.5 - (iterations * 0.1)

def damp_exp0_7(iterations):
	return 0.7**iterations

damping_funcs = {
	'lin5': damp_linear5,
	'exp': lambda i: 0.5/2**i,
	'exp_0.7': damp_exp0_7,
}

class Configuration(object):
	def __init__(self):
		self.signal = None
		self.backgrounds = None
		self.Variables = None
		self.preselection = "1"
		self.event_weight = 1.
		self.lumi = 10e3
		self.enable_plots = False
		self.rankingMethod = "sig"
		self.optimisationMethod = "sig"
		self.flatBkgUncertainty = None
		self.method = None
		self.use_validation = False # if enabled, an output tree is produced

		self.damp_func = None

def sample(name, chain, weight=1.0, color=ROOT.kBlack, MCboundary=10.):
	return Sample(name, chain, weight, color, MCboundary)

def load_config(filename):
	import utils

	Range = namedtuple("Range", "min max nBins lower_cut")

	config = Configuration()

	env = {
		"Config": config, 
		"Utils": utils, 
		"Damp": damping_funcs,
		'ROOT': ROOT,
		'Range': Range,
		'Sample': sample,
	}

	execfile(filename, env)

	return config
