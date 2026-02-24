from ROOT import gROOT,gStyle,TH2F,TLegend,TCanvas,TFile, TColor
import array, math, sys
import os
import cmsstyle as CMS
CMS.SetExtraText("Simulation")

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
 gStyle.SetLegendFont(42)
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
 #for n2 in ["withN2","noN2"]:
 # for tagger in ["_particlenetDDT",""]:
 #  for sample in ["WJets","ZJets","TTToHadronic","QCD","WJetsMatched","WJetsMatched_fakes","WJetsUnmatched"]:
 #   for year in ["UL18","UL17","UL16preVFP","UL16postVFP"]:
 #    for ptmin,ptmax in [(575,650),(650,725),(725,800),(800,1000),(1000,1200),(1200,3000)]:
 for n2,tagger,sample,year,ptmin,ptmax in [("withN2","_particlenetDDT","WJets","UL17",650,725),("withN2","_particlenetDDT","WJetsMatched","UL17",650,725),("withN2","_particlenetDDT","WJetsUnmatched","UL17",650,725)]:
      for plotname, plotlist in [("summary",["nominal",
      "pu_down","pu_up","triggersf_down","triggersf_up","prefiring",
      "jec_down","jec_up",
      "fsr_down","fsr_up","isr_down","isr_up",
      "v_qcd_down","v_qcd_up","w_ewk_down","w_ewk_up","z_ewk_down","z_ewk_up",
      "toppt_off",
      #"model_down",
      "model_up"]),
       ("summary_short",["nominal",
      #"pu_down","pu_up","triggersf_down","triggersf_up","prefiring",
      "fsr_down","fsr_up","isr_down","isr_up",
      "w_ewk_down","w_ewk_up","z_ewk_down","z_ewk_up","v_qcd_down","v_qcd_up",
      "jec_down","jec_up",
      "toppt_off",
      #"model_down",
      "model_up"]),
       #("summary_jec1",["nominal","jec_down", "jec_up",
       #"jec_AbsoluteStat_down", "jec_AbsoluteStat_up", 
       #"jec_AbsoluteScale_down", "jec_AbsoluteScale_up", 
       #"jec_AbsoluteMPFBias_down", "jec_AbsoluteMPFBias_up", 
       #"jec_Fragmentation_down", "jec_Fragmentation_up", 
       #"jec_SinglePionECAL_down", "jec_SinglePionECAL_up", 
       #"jec_SinglePionHCAL_down", "jec_SinglePionHCAL_up"]),
       #("summary_jec2",["nominal","jec_down", "jec_up",
       #"jec_FlavorQCD_down", "jec_FlavorQCD_up", 
       #"jec_TimePtEta_down", "jec_TimePtEta_up", 
       #"jec_RelativePtBB_down", "jec_RelativePtBB_up", 
       #"jec_RelativePtEC1_down", "jec_RelativePtEC1_up", 
       #"jec_RelativePtEC2_down", "jec_RelativePtEC2_up", 
       #"jec_RelativePtHF_down", "jec_RelativePtHF_up",
       #"jec_RelativeBal_down", "jec_RelativeBal_up"]),
       #("summary_jec3",["nominal","jec_down", "jec_up", 
       #"jec_RelativeFSR_down", "jec_RelativeFSR_up", 
       #"jec_RelativeSample_down", "jec_RelativeSample_up", 
       #"jec_RelativeStatFSR_down", "jec_RelativeStatFSR_up", 
       #"jec_RelativeStatEC_down", "jec_RelativeStatEC_up", 
       #"jec_RelativeStatHF_down", "jec_RelativeStatHF_up",
       #"jec_RelativeJEREC1_down", "jec_RelativeJEREC1_up", 
       #"jec_RelativeJEREC2_down", "jec_RelativeJEREC2_up"]),
       #("summary_jec4",["nominal","jec_down", "jec_up", 
       #"jec_RelativeJERHF_down", "jec_RelativeJERHF_up", 
       #"jec_PileUpDataMC_down", "jec_PileUpDataMC_up", 
       #"jec_PileUpPtRef_down", "jec_PileUpPtRef_up", 
       #"jec_PileUpPtBB_down", "jec_PileUpPtBB_up", 
       #"jec_PileUpPtEC1_down", "jec_PileUpPtEC1_up", 
       #"jec_PileUpPtEC2_down", "jec_PileUpPtEC2_up", 
       #"jec_PileUpPtHF_down", "jec_PileUpPtHF_up"])
       ]:
       print("making systematics_"+plotname+year+"_"+sample+"_"+n2+"_"+tagger+"_"+str(ptmin)+".pdf")
       files=[]
       hists=[]

       names={"nominal":"Nominal","model":"Hadronization model","jec":"Jet energy scale","isr":"Initial state radiation","fsr":"Final state radiation","w_ewk":"W+jets (NLO) EW","z_ewk":"Z+jets (NLO) EW", "v_qcd":"V+jets (NLO) QCD", "triggersf":"Trigger eff.", "pu":"Pileup", "toppt_off":"t#bar{t} (NLO)","prefiring":"Trigger pref.",
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
       
       c867=TColor( 0.341, 0.565, 0.988)
       k867=c867.GetNumber()
       c419=TColor( 0.894, 0.145, 0.212)
       k419=c419.GetNumber()
       c413=TColor( 0.973, 0.612, 0.125)
       k413=c413.GetNumber()
       c797=TColor( 0.612, 0.612, 0.631)
       k797=c797.GetNumber()
       c810=TColor( 0.478, 0.129, 0.867)
       k810=c810.GetNumber()
       c804=TColor( 0.588, 0.29, 0.545)
       k804=c804.GetNumber()
 
       if plotname=="summary_short":
         colors=[1,2,k867,k797,k419,k804,k413,k810]
       else:
         colors=[1,2,3,4,6,7,8,9,12,28,34,38,40,41,42,43,44,45,46,47,48,49]
       marker_up=[20,21,22,23,29,33,34,45,47,41,43]
       marker_down=[24,25,26,32,30,27,28,44,46,40,42]
       color=0
 
       if "WJets" in sample: samplename="W+jets"
       if sample=="ZJets": samplename="Z+jets"
       if sample=="TTToHadronic": samplename="t#bar{t}"
       if sample=="QCD": samplename="QCD"
 
       l=TLegend(0.52,0.5,0.9,0.9,samplename+", "+str(ptmin)+" < p_{T} < "+str(ptmax)+" GeV, "+year)
       #l.SetTextFont(42)
       #l.SetTitle()
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
  
           dataname="W_"+sample+"__mjet_"+str(ptmin)+"to"+str(ptmax).replace("3000","Inf")+"_inclusive"
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
             hist.GetYaxis().SetRangeUser(0.9,1.15)
           if "short" in plotname:
             hist.GetYaxis().SetRangeUser(0.6,1.8)
           else:
             hist.GetYaxis().SetRangeUser(0,2.5)
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

       if plotname=="summary" or plotname=="summary_short":
         color=1
         canvas=TCanvas("systematics"+sample, "systematics"+sample, 0, 0, 300, 300)
         canvas.cd()
       
         if "WJets" in sample: samplename="W+jets"
         if sample=="ZJets": samplename="Z+jets"
         if sample=="TTToHadronic": samplename="t#bar{t}"
         if sample=="QCD": samplename="QCD"
 
         l=TLegend(0.50,0.35,0.9,0.80,samplename+", "+str(ptmin)+" < p_{T} < "+str(ptmax).replace("3000","inf")+" GeV")
         #l.SetTextFont(42)
         #l.SetTitle()
         l.SetTextSize(0.04)
         l.SetFillStyle(0)

         l2=TLegend(0.50,0.3,0.9,0.65,"")
         #l2.SetTextFont(42)
         #l2.SetTitle()
         l2.SetTextSize(0.04)
         l2.SetFillStyle(0)

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
  
           dataname="W_"+sample+"__mjet_"+str(ptmin)+"to"+str(ptmax).replace("3000","Inf")+"_inclusive"
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
           hist.GetYaxis().SetTitle("Uncertainty [%]")
           hist.GetYaxis().SetRangeUser(0,38)
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
          
         c=0
         for sys in reversed(plotlist):
           c+=1
           if "down" in sys or sys=="nominal" or not sys in histlist.keys(): continue
           #if c<10:
           l.AddEntry(histlist[sys],names[sys.replace("_up","")],"pl")
           #else:
           #  l2.AddEntry(histlist[sys],names[sys.replace("_up","")],"pl")
        
         l.Draw("same")
         #l2.Draw("same")
               
         CMS.CMS_lumi(canvas, 0)
         canvas.Modified()
         canvas.Update()
         canvas.RedrawAxis()
         canvas.GetFrame().Draw()
         canvas.SaveAs("systematics_stack_"+plotname+year+"_"+sample+"_"+n2+"_"+tagger+"_"+str(ptmin)+".pdf")
