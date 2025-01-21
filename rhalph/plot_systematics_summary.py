from ROOT import gROOT,gStyle,TH2F,TLegend,TCanvas,TFile
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
 for n2 in ["withN2","noN2"]:
  for tagger in ["_particlenetDDT",""]:
   for sample in ["WJets","WJetsMatched","WJetsMatched_fakes","WJetsUnmatched","ZJets","TTToHadronic","QCD"]:
    for year in ["UL18","UL17","UL16preVFP","UL16postVFP"]:
     for ptmin,ptmax in [(650,725),(725,800),(800,1000),(1000,1200)]:
      for plotname, plotlist in [("summary",["nominal","fsr_down","fsr_up","isr_down","isr_up","jec_down","jec_up",
      "pu_down","pu_up","triggersf_down","triggersf_up","toppt_off",
      "v_qcd_down","v_qcd_up","w_ewk_down","w_ewk_up","z_ewk_down",
      "z_ewk_up","model_up","prefiring"]),
       ("summary_jec1",["nominal","jec_down", "jec_up",
       "jec_AbsoluteStat_down", "jec_AbsoluteStat_up", 
       "jec_AbsoluteScale_down", "jec_AbsoluteScale_up", 
       "jec_AbsoluteMPFBias_down", "jec_AbsoluteMPFBias_up", 
       "jec_Fragmentation_down", "jec_Fragmentation_up", 
       "jec_SinglePionECAL_down", "jec_SinglePionECAL_up", 
       "jec_SinglePionHCAL_down", "jec_SinglePionHCAL_up", 
       "jec_FlavorQCD_down", "jec_FlavorQCD_up", 
       "jec_TimePtEta_down", "jec_TimePtEta_up", 
       "jec_RelativePtBB_down", "jec_RelativePtBB_up", 
       "jec_RelativePtEC1_down", "jec_RelativePtEC1_up", 
       "jec_RelativePtEC2_down", "jec_RelativePtEC2_up", 
       "jec_RelativePtHF_down", "jec_RelativePtHF_up"]),
       ("summary_jec2",["nominal","jec_down", "jec_up",
       "jec_RelativeBal_down", "jec_RelativeBal_up", 
       "jec_RelativeFSR_down", "jec_RelativeFSR_up", 
       "jec_RelativeSample_down", "jec_RelativeSample_up", 
       "jec_RelativeStatFSR_down", "jec_RelativeStatFSR_up", 
       "jec_RelativeStatEC_down", "jec_RelativeStatEC_up", 
       "jec_RelativeStatHF_down", "jec_RelativeStatHF_up", 
       "jec_RelativeJEREC1_down", "jec_RelativeJEREC1_up", 
       "jec_RelativeJEREC2_down", "jec_RelativeJEREC2_up", 
       "jec_RelativeJERHF_down", "jec_RelativeJERHF_up", 
       "jec_PileUpDataMC_down", "jec_PileUpDataMC_up", 
       "jec_PileUpPtRef_down", "jec_PileUpPtRef_up", 
       "jec_PileUpPtBB_down", "jec_PileUpPtBB_up", 
       "jec_PileUpPtEC1_down", "jec_PileUpPtEC1_up", 
       "jec_PileUpPtEC2_down", "jec_PileUpPtEC2_up", 
       "jec_PileUpPtHF_down", "jec_PileUpPtHF_up"])]:
       print("making systematics_"+plotname+year+"_"+sample+"_"+n2+"_"+tagger+"_"+str(ptmin)+".pdf")
       files=[]
       hists=[]
 
       canvas=TCanvas("systematics"+sample, "systematics"+sample, 0, 0, 300, 300)
       canvas.cd()
       
       colors=[1,2,3,4,6,7,8,9,12,28,34,38,40,41,42,43,44,45,46,47,48,49]
       marker_up=[20,21,22,23,29,33,34,45,47,41,43]
       marker_down=[24,25,26,32,30,27,28,44,46,40,42]
       color=0
 
       if "WJets" in sample: samplename="W+Jets"
       if sample=="ZJets": samplename="Z+Jets"
       if sample=="TTToHadronic": samplename="t#bar{t}"
       if sample=="QCD": samplename="QCD"
 
       l=TLegend(0.40,0.65,0.95,0.93,samplename+", "+str(ptmin)+"<p_{T}<"+str(ptmax)+" GeV, "+year)
       l.SetTextSize(0.035)
       l.SetFillStyle(0)

       for sys in plotlist:
           if not sample=="ZJets" and "z_" in sys:continue
           if not "WJets" in sample and ("w_" in sys or "model" in sys):continue
           if not "Jets" in sample and "v_" in sys:continue
           if not sample=="TTToHadronic" and "toppt_" in sys:continue
           filename="../python/flat_templates_"+n2+"/templates_"+year+tagger+"_1d_unfolding"+("_"+sys if sys!="nominal" else "")+".root"
           try:
             f=TFile.Open(filename)
           except:
             print("missing file", filename)
             continue
           print("File:",filename)
           files+=[f]
  
           dataname="W_"+sample+"__mjet_"+str(ptmin)+"to"+str(ptmax)+"_inclusive"
           print("Hist Name:",dataname)
           hist=f.Get(dataname).Clone(dataname+n2+tagger+str(ptmin))
           hist=rebin(hist,binning)
           if sys=="nominal": histref=hist.Clone(dataname+n2+tagger+str(ptmin)+"ref")
           print(hist.Integral(),histref.Integral())
           hist.Divide(histref)
           hist.GetXaxis().SetTitle("Softdrop Mass (GeV)")
           hist.GetYaxis().SetTitle("Ratio to nominal")
           if "jec" in plotname:
             hist.GetYaxis().SetRangeUser(0.85,1.2)
           else:
             hist.GetYaxis().SetRangeUser(0.6,1.5)
           hist.SetTitle("")
           hists+=[hist]
  
           #hist.SetLineWidth(1)
           hist.SetLineColor(colors[color])
           hist.SetLineStyle(color%5)
           hist.SetMarkerStyle(marker_up[color%len(marker_up)] if "up" in sys else marker_down[color%len(marker_up)])
           hist.SetMarkerColor(colors[color])
           hist.SetLineWidth(1+int(color/len(marker_up)))
     
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
             
       canvas.SaveAs("systematics_"+plotname+year+"_"+sample+"_"+n2+"_"+tagger+"_"+str(ptmin)+".pdf")
