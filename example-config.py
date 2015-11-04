
Config.Variables = {
	"met": Range(0, 800000, 100, False),
	#"amt2": Range(0, 1200, 100, False),
 	#"mt": Range(0, 1000000, 100, False),
 	#"ht": Range(0, 2500000, 100, False),
 	#"m_top_chi2": Range(0, 2000, 100, False),
	#"met_perp": Range(0, 1000000, 100, False),
	"topness": Range(-25, 25, 100, False),
}

Config.signal = Sample("stop_600_300", Utils.load_chain(["testSamples/default13/stop_600_300/*.root"], "CollectionTree"), color=ROOT.kRed)
Config.backgrounds = [
	Sample("ttbar", Utils.load_chain(["testSamples/default13/ttbar1/*.root"], "CollectionTree"), color=ROOT.kBlue),
	Sample("ttV", Utils.load_chain(["testSamples/default13/ttV/*.root"], "CollectionTree"), color=ROOT.kGreen),
	Sample("Wjets", Utils.load_chain(["testSamples/default13/wjets/*.root"], "CollectionTree"), color=ROOT.kOrange),
]

Config.event_weight = "(weight*xs_weight)"
Config.preselection = "(n_jet>=4) && (jet_pt[0]>80000) && (jet_pt[1]>60000) && (jet_pt[2]>40000) && (jet_pt[3]>25000) && (mt>60000) && (n_bjet>0)"
Config.rankingMethod = "sig"
Config.optimisationMethod = "sig"
#Config.flatBkgUncertainty = 0.2
Config.enable_plots = True
#Config.use_validation = True 

#Config.damp_func = Damp["lin5"]
