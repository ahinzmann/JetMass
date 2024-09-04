from ROOT import *
import ROOT
import array, math, sys
import os

def rebin(h1,binning):
    for b in range(h1.GetXaxis().GetNbins()):
        h1.SetBinContent(b+1,h1.GetBinContent(b+1)*h1.GetBinWidth(b+1))
        h1.SetBinError(b+1,h1.GetBinError(b+1)*h1.GetBinWidth(b+1))
    h1=h1.Rebin(len(binning)-1,h1.GetName()+"_rebin",binning)
    for b in range(h1.GetXaxis().GetNbins()):
        h1.SetBinContent(b+1,h1.GetBinContent(b+1)/h1.GetBinWidth(b+1))
        h1.SetBinError(b+1,h1.GetBinError(b+1)/h1.GetBinWidth(b+1))
    return h1
    
if __name__=="__main__":
  print("start ROOT")
  #gROOT.Reset()
  gROOT.SetStyle("Plain")
  gROOT.SetBatch(True)
  gStyle.SetOptStat(0)
  gStyle.SetOptFit(0)
  gStyle.SetTitleOffset(1.2,"Y")
  gStyle.SetPadLeftMargin(0.15)
  gStyle.SetPadBottomMargin(0.11)
  gStyle.SetPadTopMargin(0.05)
  gStyle.SetPadRightMargin(0.05)
  gStyle.SetMarkerSize(2.5)
  gStyle.SetHistLineWidth(1)
  gStyle.SetStatFontSize(0.020)
  gStyle.SetTitleSize(0.06, "XYZ")
  gStyle.SetLabelSize(0.05, "XYZ")
  gStyle.SetLegendBorderSize(0)
  gStyle.SetPadTickX(1)
  gStyle.SetPadTickY(1)
  gStyle.SetEndErrorSize(5)
  
  binning=array.array('d')
  for n in range(21):
      binning.append(50+n*9)
  
  for sample in ["WJets","ZJets","TTToHadronic","QCD"]:
  
    files=[]
    hists=[]

    canvas=TCanvas("systematics"+sample, "systematics"+sample, 0, 0, 300, 300)
    canvas.cd()
    
    colors=[1,2,3,4,6,7,8,9,12,28,34,38,40,41,42,43,44,45,46,47,48,49]
    color=0

    if sample=="WJets": samplename="W+Jets"
    if sample=="ZJets": samplename="Z+Jets"
    if sample=="TTToHadronic": samplename="t#bar{t}"
    if sample=="QCD": samplename="QCD"

    l=TLegend(0.40,0.65,0.95,0.93,samplename+", 650<p_{T}<725 GeV, UL18")
    l.SetTextSize(0.035)
    l.SetFillStyle(0)

    for sys in ["nominal","fsr_down","fsr_up","isr_down","isr_up","jec_down","jec_up","pu_down","pu_up","triggersf_down","triggersf_up","toppt_off","v_qcd_down","v_qcd_up","w_ewk_down","w_ewk_up","z_ewk_down","z_ewk_up"]:
        if not sample=="ZJets" and "z_" in sys:continue
        if not sample=="WJets" and "w_" in sys:continue
        if not sample=="Jets" and "v_" in sys:continue
        if not sample=="TTToHadronic" and "toppt_" in sys:continue
        filename="../../JetMassFits/flat_templates/templates_UL18_particlenetDDT_1d_unfolding"+("_"+sys if sys!="nominal" else "")+".root"
        f=TFile.Open(filename)
        print("File:",filename)
        files+=[f]

        dataname="W_"+sample+"__mjet_650to725_inclusive"
        print("Hist Name:",dataname)
        hist=f.Get(dataname)
        hist=rebin(hist,binning)
        if sys=="nominal": histref=hist.Clone("ref")
        hist.Divide(histref)
        hist.GetXaxis().SetTitle("Softdrop Mass (GeV)")
        hist.GetYaxis().SetTitle("Ratio to nominal")
        hist.GetYaxis().SetRangeUser(0.85,1.4)
        hist.SetTitle("")
        hists+=[hist]

        #hist.SetLineWidth(1)
        hist.SetLineColor(colors[color])
        hist.SetLineStyle(color%5)
        hist.SetMarkerStyle(20+color)
        hist.SetMarkerColor(colors[color])

        if sys=="nominal":
          hist.Draw("hist")
        else:
          hist.Draw("histplsame")
              
        if not "down" in sys:
          if sys=="nominal":
            l.AddEntry(hist,sys.replace("_up",""),"l")
          else:
            l.AddEntry(hist,sys.replace("_up",""),"pl")
          color+=1

    l.Draw("same")
          
    canvas.SaveAs("systematics_summary_"+sample+".pdf")
