from ROOT import *

# this style is initialized below
Style = TStyle("SWup","Modified ATLAS style")

TitleEvents = "events"
TitleNorm = "event fraction"

YMaxFactorLin = 1.3

OBJECTS = []

def legend(leg):
	leg.SetFillColor(kWhite)

def single_hist(hist):
	hist.SetLineColor(kBlack)
	hist.SetLineWidth(3)
	hist.SetFillColor(kGray)

def comp_hist(hist):
	hist.SetLineWidth(3)

def string(x, y, text, rel=None):
	obj = TLatex(x, y, text)
	obj.SetNDC()
	if rel:
		obj.SetTextSize(rel * obj.GetTextSize())
	obj.Draw("same")

	global OBJECTS
	OBJECTS.append(obj)

def _init_style():
	global Style
	# use plain black on white colors
	Style.SetOptStat(0)
	_icol=0
	Style.SetFrameBorderMode(_icol)
	Style.SetCanvasBorderMode(_icol)
	Style.SetPadBorderMode(_icol) 
	Style.SetPadColor(_icol)
	Style.SetCanvasColor(_icol)
	Style.SetStatColor(_icol)
	Style.SetPaperSize(20,26)
	Style.SetPadTopMargin(0.05)
	Style.SetPadRightMargin(0.05)
	Style.SetPadBottomMargin(0.16)
	Style.SetPadLeftMargin(0.16)
	Style.SetFrameFillColor(_icol)

	_font=42
	_tsize=0.06
	Style.SetTextFont(_font)
	Style.SetTextSize(_tsize)
	Style.SetLabelFont(_font, "x")
	Style.SetTitleFont(_font, "x")
	Style.SetLabelFont(_font, "y")
	Style.SetTitleFont(_font, "y")
	Style.SetLabelFont(_font, "z")
	Style.SetTitleFont(_font, "z")
	Style.SetLabelSize(_tsize, "x")
	Style.SetTitleSize(_tsize, "x")
	Style.SetLabelSize(_tsize, "y")
	Style.SetTitleSize(_tsize, "y")
	Style.SetLabelSize(_tsize, "z")
	Style.SetTitleSize(_tsize, "z")
	Style.SetMarkerStyle(20)
	Style.SetMarkerSize(1.2)
	Style.SetHistLineWidth(2)
	Style.SetLineStyleString(2, "[12 12]")
	Style.SetEndErrorSize(0.)
	Style.SetEndErrorSize(5)
	Style.SetOptTitle(0)
	Style.SetOptFit(0)
	Style.SetPadTickX(1)
	Style.SetPadTickY(1)

	Style.SetTitleXOffset(1.2)
	Style.SetTitleYOffset(1.3)

	Style.SetPalette(53)

	TGaxis.SetMaxDigits(4)

	gROOT.SetStyle("SWup")
	gROOT.ForceStyle()

_init_style()
