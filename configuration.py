class Configuration(object):
	def __init__(self):
		self.sigTree = None
		self.bkgTreeList = None
		self.Variables = None
		self.preselection = "1"
		self.event_weight = 1.
		self.enable_plots = False
		self.rankingMethod = "sig"
		self.optimisationMethod = "sig"
		self.method = None
		self.use_validation = False
