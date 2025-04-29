from ROOT import gROOT,gStyle,TH2F,TLegend,TCanvas,TFile
import array, math, sys
import os
import cmsstyle as CMS
CMS.SetExtraText("Simulation Preliminary")

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

 CMS.SetLumi("")
 CMS.SetEnergy("13")
 CMS.ResetAdditionalInfo()
 CMS.setCMSStyle()

 gStyle.SetOptStat(0)
 gStyle.SetOptFit(0)
 gStyle.SetTitleOffset(1.2,"Y")
 gStyle.SetPadLeftMargin(0.15)
 gStyle.SetPadBottomMargin(0.15)
 gStyle.SetPadTopMargin(0.08)
 gStyle.SetPadRightMargin(0.05)
 gStyle.SetMarkerSize(0.7)
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
   for sample in ["WJets","ZJets","TTToHadronic","QCD","WJetsMatched","WJetsMatched_fakes","WJetsUnmatched"]:
    for year in ["UL18","UL17","UL16preVFP","UL16postVFP"]:
     for ptmin,ptmax in [(650,725),(725,800),(800,1000),(1000,1200)]:
      for plotname, plotlist in [("summary",["nominal",
      "pu_down","pu_up","triggersf_down","triggersf_up","prefiring",
      "jec_down","jec_up",
      "fsr_down","fsr_up","isr_down","isr_up",
      "v_qcd_down","v_qcd_up","w_ewk_down","w_ewk_up","z_ewk_down","z_ewk_up",
      "toppt_off",
      "model_up"]),
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

       names={"nominal":"Nominal","model":"Model","jec":"Jet energy scale","isr":"Initial state shower","fsr":"Final state shower","w_ewk":"W+jets (NLO) EW","z_ewk":"Z+jets (NLO) EW", "v_qcd":"V+jets (NLO) QCD", "triggersf":"Trigger eff.", "pu":"Pileup", "toppt_off":"t#bar{t} (NLO)","prefiring":"Trigger pref.",
       "jec_AbsoluteStat":"JEC AbsoluteStat", 
       "jec_AbsoluteScale":"JEC AbsoluteScale", 
       "jec_AbsoluteMPFBias":"JEC AbsoluteMPFBias", 
       "jec_Fragmentation":"JEC Fragmentation", 
       "jec_SinglePionECAL":"JEC SinglePionECAL", 
       "jec_SinglePionHCAL":"JEC SinglePionHCAL", 
       "jec_FlavorQCD":"JEC FlavorQCD", 
       "jec_TimePtEta":"JEC TimePtEta", 
       "jec_RelativePtBB":"JEC RelativePtBB", 
       "jec_RelativePtEC1":"JEC RelativePtEC1", 
       "jec_RelativePtEC2":"JEC RelativePtEC2", 
       "jec_RelativePtHF":"JEC RelativePtHF",
       "jec_RelativeBal":"JEC RelativeBal",
       "jec_RelativeFSR":"JEC RelativeFSR", 
       "jec_RelativeSample":"JEC RelativeSample", 
       "jec_RelativeStatFSR":"JEC RelativeStatFSR", 
       "jec_RelativeStatEC":"JEC RelativeStatEC", 
       "jec_RelativeStatHF":"JEC RelativeStatHF", 
       "jec_RelativeJEREC1":"JEC RelativeJEREC1", 
       "jec_RelativeJEREC2":"JEC RelativeJEREC2", 
       "jec_RelativeJERHF":"JEC RelativeJERHF", 
       "jec_PileUpDataMC":"JEC PileUpDataMC", 
       "jec_PileUpPtRef":"JEC PileUpPtRef", 
       "jec_PileUpPtBB":"JEC PileUpPtBB", 
       "jec_PileUpPtEC1":"JEC PileUpPtEC1", 
       "jec_PileUpPtEC2":"JEC PileUpPtEC2", 
       "jec_PileUpPtHF":"JEC PileUpPtHF",
       }
 
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
 
       l=TLegend(0.52,0.5,0.9,0.9,samplename+", "+str(ptmin)+"<p_{T}<"+str(ptmax)+" GeV, "+year)
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
           if "jec" in sys or "isr" in sys or "fsr" in sys:
             hist.Smooth(1,"R")
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
               l.AddEntry(hist,names[sys.replace("_up","")],"l")
             else:
               l.AddEntry(hist,names[sys.replace("_up","")],"pl")
             color+=1
     
       l.Draw("same")
             
       canvas.SaveAs("systematics_"+plotname+year+"_"+sample+"_"+n2+"_"+tagger+"_"+str(ptmin)+".pdf")

       if plotname=="summary":
         color=1
         canvas=TCanvas("systematics"+sample, "systematics"+sample, 0, 0, 300, 300)
         canvas.cd()
       
         if "WJets" in sample: samplename="W+Jets"
         if sample=="ZJets": samplename="Z+Jets"
         if sample=="TTToHadronic": samplename="t#bar{t}"
         if sample=="QCD": samplename="QCD"
 
         l=TLegend(0.52,0.5,0.9,0.9,samplename+", "+str(ptmin)+"<p_{T}<"+str(ptmax)+" GeV")
         l.SetTextSize(0.04)
         l.SetFillStyle(0)

         stack=None
         histlist={}
         for sys in plotlist:
           if "down" in sys: continue
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
           if "jec" in sys or "isr" in sys or "fsr" in sys:
             hist.Smooth(1,"R")
           for b in range(hist.GetNbinsX()):
             hist.SetBinContent(b+1,math.sqrt(pow((hist.GetBinContent(b+1)-1.)*100.,2)))
             if stack==None:
               stack=hist
             else:
               stack.SetBinContent(b+1,math.sqrt(pow(stack.GetBinContent(b+1),2)+pow(hist.GetBinContent(b+1),2)))
           hist.GetXaxis().SetTitle("m_{SD} [GeV]")
           hist.GetYaxis().SetTitle("Uncertainty in %")
           hist.GetYaxis().SetRangeUser(0,50)
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
           histlist[sys]=hist
                 
           color+=1
     
         stack.SetLineColor(1)
         stack.SetLineStyle(1)
         stack.SetLineWidth(2)
         stack.SetMarkerSize(0)
         stack.Draw("lsame")
         l.AddEntry(stack,"Total","l")

         for sys in reversed(plotlist):
           if "down" in sys or sys=="nominal" or not sys in histlist.keys(): continue
           l.AddEntry(histlist[sys],names[sys.replace("_up","")],"pl")
         
         l.Draw("same")
               
         CMS.CMS_lumi(canvas, 0)
         canvas.Modified()
         canvas.Update()
         canvas.RedrawAxis()
         canvas.GetFrame().Draw()
         canvas.SaveAs("systematics_stack_"+plotname+year+"_"+sample+"_"+n2+"_"+tagger+"_"+str(ptmin)+".pdf")
