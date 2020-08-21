massvar = "( ((rrw_n_btag[0]==0)*rrw_m[0]) + ((rrw_n_btag[0]==1 && Alt$(rrw_n_btag[1],1)==0 )*Alt$(rrw_m[1],0)) )"
Config.Variables = {
	"met": Range(0, 500000, 100, False),
	"amt2": Range(100, 400, 60, False),
 	"mt": Range(0, 300000, 30, False),
 	"jet_pt[0]": Range(0, 250000, 50, False),
 	"jet_pt[1]": Range(0, 250000, 50, False),
 	"jet_pt[2]": Range(0, 250000, 50, False),
 	"jet_pt[3]": Range(0, 250000, 50, False),
 	"bjet_pt[0]": Range(0, 250000, 50, False),
 	"bjet_pt[1]": Range(0, 250000, 50, False),
 	"ht_sig": Range(0, 30, 30, False),
	"dphi_jet0_ptmiss": Range(0, 3, 30, False),
	"dphi_jet1_ptmiss": Range(0, 3, 30, False),
	"dphi_met_lep": Range(0, 3, 30, False),
	"hadw_cand_m[0]": Range(0, 100000, 20, False),
}

Config.signal = Sample("stop_600_300", Utils.load_chain(["/afs/cern.ch/work/j/jmontejo/stop1l-xaod/export/default_wtag/stop_bC_600_500_250/*.root"], ["stop_bC_600_500_250_Nom"]), color=ROOT.kRed)
Config.backgrounds = [
	Sample("ttbar", Utils.load_chain(["/afs/cern.ch/work/j/jmontejo/stop1l-xaod/export/default_wtag/powheg_ttbar/*.root"], "powheg_ttbar_Nom"), color=ROOT.kBlue),
	Sample("singletop", Utils.load_chain(["/afs/cern.ch/work/j/jmontejo/stop1l-xaod/export/default_wtag/powheg_singletop/*.root"], "powheg_singletop_Nom"), color=ROOT.kBlue),
	Sample("ttV", Utils.load_chain(["/afs/cern.ch/work/j/jmontejo/stop1l-xaod/export/default_wtag/madgraph_ttV/*.root"], "madgraph_ttV_Nom"), color=ROOT.kBlue),
]

Config.event_weight = "(xs_weight*weight)"
Config.preselection = "(n_jet>=4) && (jet_pt[0]>50000) && (jet_pt[1]>40000) && (jet_pt[2]>25000) && (jet_pt[3]>25000) && (mt>160e3) && (ht_sig>7) && (n_bjet>=2) && (amt2>170) && (met>230e3) && (((mT2tauLooseTau_GeV>=0)?mT2tauLooseTau_GeV:300)>80) && stxe_trigger && (dphi_jet0_ptmiss>0.4) && (dphi_jet1_ptmiss>0.4) && (n_hadw_cand>=1)"
Config.rankingMethod = "roostats"
Config.optimisationMethod = "roostats"
Config.flatBkgUncertainty = 0.2
Config.includeMCstat = True
Config.enable_plots = True
Config.lumi = 36500
#Config.use_validation = True 

Config.damp_func = Damp["exp_0.8"]
