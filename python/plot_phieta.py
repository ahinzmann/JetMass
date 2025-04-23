import os, sys
from ROOT import * 
import array
from math import *

#gROOT.Macro( os.path.expanduser( '~/rootlogon.C' ) )
#gROOT.Reset()
gROOT.SetStyle("Plain")
gROOT.SetBatch(True)
gStyle.SetOptStat(0)
#gStyle.SetOpt(0)
gStyle.SetTitleOffset(1.2,"Y")
gStyle.SetPadLeftMargin(0.18)
gStyle.SetPadBottomMargin(0.15)
gStyle.SetPadTopMargin(0.03)
gStyle.SetPadRightMargin(0.05)
gStyle.SetMarkerSize(1.5)
gStyle.SetHistLineWidth(1)
gStyle.SetStatFontSize(0.020)
gStyle.SetTitleSize(0.06, "XYZ")
gStyle.SetLabelSize(0.05, "XYZ")
gStyle.SetNdivisions(510, "XYZ")
gStyle.SetLegendBorderSize(0)

if __name__ == '__main__':

 for year in ["UL16postVFP","UL16preVFP","UL17","UL18"]:
  for sample in ["Data","QCD"]:

    canvas = TCanvas("","",0,0,600,600)
    canvas.SetRightMargin(0.2)
    plots=[]
    legends=[]
    new_hists=[]

    filename="flat_templates/templates_"+year+"_particlenetDDT_1d_unfolding.root"
    print(filename)
    f = TFile.Open(filename)
    histname="W_"+sample+"_phieta"
    print(histname)
    h=f.Get(histname)
    bins=h.GetNbinsX()
    print(bins)
    binsx=array.array('d')
    binsy=array.array('d')
    for i in range(100):
      binsx.append(h.GetXaxis().GetBinLowEdge(i+50*100-50+1))
    binsx.append(h.GetXaxis().GetBinUpEdge(50*100+50))
    for j in range(100):
      binsy.append(h.GetXaxis().GetBinLowEdge(j*100+1)/100)
    binsy.append(h.GetXaxis().GetBinUpEdge(100*100)/100)
    print(binsx.tolist())
    print(binsy.tolist())
    print([h.GetBinContent(i+1+50*100-50) for i in range(100)])
    gStyle.SetNumberContours(200)
    gStyle.SetPalette(104)
    h2=TH2D("2d","",len(binsx)-1,binsx,len(binsy)-1,binsy)
    for i in range(len(binsx)-1):
      for j in range(len(binsy)-1):
        h2.SetBinContent(i+1,j+1,h.GetBinContent(i-50+100*j+1))
        #print(i,j,h2.GetBinContent(i+1,j+1))
    h2.GetXaxis().SetTitle("Jet #phi")
    h2.GetYaxis().SetTitle("Jet #eta")
    h2.Draw("colz")
    l=TLegend(0.25,0.9,1.0,0.95,sample)
    l.SetTextSize(0.033)
    l.SetFillStyle(0)
    l.Draw("same")
    l2=TLegend(0.55,0.9,1.0,0.95,year)
    l2.SetTextSize(0.033)
    l2.SetFillStyle(0)
    l2.Draw("same")
    h2.GetZaxis().SetRangeUser(0,7000)#h2.GetMaximum()*1.2)
    canvas.SaveAs("flat_templates/phieta_"+sample+"_"+year+".pdf")
