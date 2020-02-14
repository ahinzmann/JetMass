import ROOT
from ROOT import gROOT,gStyle
gROOT.SetBatch(True)
gStyle.SetOptStat(0)
gStyle.SetOptFit(0)
gStyle.SetOptTitle(0)

gStyle.SetTextFont(43)

gStyle.SetTitleOffset(0.86,"X")
gStyle.SetTitleOffset(1.6,"Y")
# gStyle.SetPadLeftMargin(0.18)
gStyle.SetPadLeftMargin(0.15)
# gStyle.SetPadBottomMargin(0.15)
gStyle.SetPadBottomMargin(0.12)
gStyle.SetPadTopMargin(0.08)
# gStyle.SetPadRightMargin(0.08)
gStyle.SetPadRightMargin(0.1)
gStyle.SetMarkerSize(0.5)
gStyle.SetHistLineWidth(2)
gStyle.SetTitleSize(0.05, "XYZ")
gStyle.SetLabelSize(0.04, "XYZ")
gStyle.SetNdivisions(506, "XYZ")
gStyle.SetLegendBorderSize(0)

useMC=True

# dir_suffix = '/PFMassMap/'
dir_suffix = ''

f_qcd = ROOT.TFile('../../Histograms/W/'+dir_suffix+'QCD.root','read')
f_data = ROOT.TFile('../../Histograms/W/'+dir_suffix+'Data.root','read')
f_wmatched = ROOT.TFile('../../Histograms/W/'+dir_suffix+'WMatched.root','read')
f_wunmatched = ROOT.TFile('../../Histograms/W/'+dir_suffix+'WUnmatched.root','read')
f_z = ROOT.TFile('../../Histograms/W/'+dir_suffix+'Z.root','read')
for useMC in [True,False]:
    ptbins =[500,550,600,675,800,1200]
    for i in range(len(ptbins)-1):
        hist_name='JetMass_N2DDT_pt%iTo%i'%(ptbins[i],ptbins[i+1])+'_%s/Mass_central'
        if(useMC): 
            h_pass = f_qcd.Get(hist_name%'pass')
            h_fail = f_qcd.Get(hist_name%'fail')       
        else:
            h_pass = f_data.Get(hist_name%'pass')
            h_pass.Add(f_wmatched.Get(hist_name%'pass'),-1)
            h_pass.Add(f_z.Get(hist_name%'pass'),-1)
            h_pass.Add(f_wunmatched.Get(hist_name%'pass'),-1)
            h_fail = f_data.Get(hist_name%'fail')
            h_fail.Add(f_z.Get(hist_name%'fail'),-1)
            h_fail.Add(f_wmatched.Get(hist_name%'fail'),-1)
            h_fail.Add(f_wunmatched.Get(hist_name%'fail'),-1)
            
        h_pass.Scale(1./h_pass.Integral())
        h_fail.Scale(1./h_fail.Integral())

        c = ROOT.TCanvas('c%i'%i,'c%i'%i,700,600)
        legend = ROOT.TLegend(0.60,0.78,0.83,0.90)
        
        h_pass.SetTitle('QCD shape comparison %i GeV < p_{T} < %i GeV'%(ptbins[i],ptbins[i+1]))
        h_pass.SetLineColor(8)
        h_pass.SetLineWidth(2)
        h_fail.SetLineColor(46)
        h_fail.SetLineWidth(2)
        h_fail.GetXaxis().SetTitle('m_{SD}')
        h_fail.GetYaxis().SetTitle('#DeltaN/N')
        h_fail.GetYaxis().SetRangeUser(0,0.03 )
        legend.AddEntry(h_pass,'QCD pass %s'%('' if useMC else '(Data-W-Z)'),'l')
        legend.AddEntry(h_fail,'QCD fail %s'%('' if useMC else '(Data-W-Z)'),'l')
        
        h_fail.Draw('H')
        h_pass.Draw('HSAME')
        latex = ROOT.TLatex()
        latex.SetNDC(1)
        latex.SetTextSize(20)
        latex.DrawLatex(0.20,0.80,"%.0f GeV #leq p_{T} < %.0f GeV"%(ptbins[i],ptbins[i+1]))
        
        legend.Draw('SAME')
        # import os
        # if(not os.path.isdir('../../Plots/'+map_name)):
        #     os.mkdir('../../Plots/'+map_name)
        # c.SaveAs('../../Plots/%s/qcd_shape_comp_%iTo%i%s.pdf'%(map_name,ptbins[i],ptbins[i+1],"" if useMC else "_fromData"))
        c.SaveAs('../../Plots/'+dir_suffix+'qcd_shape_comp_%iTo%i%s.pdf'%(ptbins[i],ptbins[i+1],"" if useMC else "_fromData"))
