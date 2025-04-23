# acceptance plots
python acceptance_efficiency.py --year UL16preVFP --load --outdir coffea_hists_withN2/acceptance_efficiency_plots_n2_0p2 --n2cut 0.2
python acceptance_efficiency.py --year UL16postVFP --load --outdir coffea_hists_withN2/acceptance_efficiency_plots_n2_0p2 --n2cut 0.2
python acceptance_efficiency.py --year UL17 --load --outdir coffea_hists_withN2/acceptance_efficiency_plots_n2_0p2 --n2cut 0.2
python acceptance_efficiency.py --year UL18 --load --outdir coffea_hists_withN2/acceptance_efficiency_plots_n2_0p2 --n2cut 0.2
ls /data/dust/user/hinzmann/jetmass/JetMass/python/coffea_hists_withN2/acceptance_efficiency_plots_n2_0p2/acceptance_*.pdf

python acceptance_efficiency.py --year UL16preVFP --load --outdir coffea_hists_noN2/acceptance_efficiency_plots_no_n2 --n2cut 0.2
python acceptance_efficiency.py --year UL16postVFP --load --outdir coffea_hists_noN2/acceptance_efficiency_plots_no_n2 --n2cut 0.2
python acceptance_efficiency.py --year UL17 --load --outdir coffea_hists_noN2/acceptance_efficiency_plots_no_n2 --n2cut 0.2
python acceptance_efficiency.py --year UL18 --load --outdir coffea_hists_noN2/acceptance_efficiency_plots_no_n2 --n2cut 0.2
ls /data/dust/user/hinzmann/jetmass/JetMass/python/coffea_hists_noN2/acceptance_efficiency_plots_no_n2/acceptance_*.pdf

# eta-phi maps
#python condor.py #./submit_jms_templates.sh 0 nominal particlenetDDT
#./flatten_templates _particlenetDDT
#python plot_phieta.py

# impacts
#python plots_april_2024.py

# postfit plots
python plots_april_2024.py
ls /data/dust/user/hinzmann/jetmass/JetMass/rhalph/UnfoldingParticleNet_N2Cut_18-09-24/FullRunII//plots/fit_shapes/*.pdf
