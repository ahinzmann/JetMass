# acceptance plots
python acceptance_efficiency.py --year UL16preVFP --load --outdir coffea_hists_withN2/acceptance_efficiency_plots_n2_0p2 --n2cut 0.2 &
python acceptance_efficiency.py --year UL16postVFP --load --outdir coffea_hists_withN2/acceptance_efficiency_plots_n2_0p2 --n2cut 0.2 &
python acceptance_efficiency.py --year UL17 --load --outdir coffea_hists_withN2/acceptance_efficiency_plots_n2_0p2 --n2cut 0.2 &
python acceptance_efficiency.py --year UL18 --load --outdir coffea_hists_withN2/acceptance_efficiency_plots_n2_0p2 --n2cut 0.2 &
ls /data/dust/user/hinzmann/jetmass/JetMass/python/coffea_hists_withN2/acceptance_efficiency_plots_n2_0p2/acceptance_*.pdf

python acceptance_efficiency.py --year UL16preVFP --load --outdir coffea_hists_noN2/acceptance_efficiency_plots_no_n2 &
python acceptance_efficiency.py --year UL16postVFP --load --outdir coffea_hists_noN2/acceptance_efficiency_plots_no_n2 &
python acceptance_efficiency.py --year UL17 --load --outdir coffea_hists_noN2/acceptance_efficiency_plots_no_n2 &
python acceptance_efficiency.py --year UL18 --load --outdir coffea_hists_noN2/acceptance_efficiency_plots_no_n2 &
ls /data/dust/user/hinzmann/jetmass/JetMass/python/coffea_hists_noN2/acceptance_efficiency_plots_no_n2/acceptance_*.pdf

# eta-phi maps
#python condor.py #./submit_jms_templates.sh 0 nominal particlenetDDT
#./flatten_templates _particlenetDDT
#python plot_phieta.py

# impacts
#python plots_april_2024.py

# uncertainty plots
python plot_systematics_summary.py

# postfit plots
condor_submit -i request_memory=8GB
source ~hinzmann/startWjetmassAnalysis.sh

python plots_april_2024.py # fitplotter/plot_stack_fit_result.py ../python/plotter.py ../python/cms_style.py
ls /data/dust/user/hinzmann/jetmass/JetMass/rhalph/UnfoldingParticleNet_N2Cut_18-09-24/FullRunII//plots/fit_shapes/*.pdf

# berstein plot
python pretty_qcdbernstein.py ../rhalph/UnfoldingParticleNet_N2Cut_18-09-24/FullRunII/ --data
ls /data/dust/user/hinzmann/jetmass/JetMass/rhalph/UnfoldingParticleNet_N2Cut_18-09-24/FullRunII//plots/pretty*.pdf

# migration matrix plot
python pretty_postfit.py --data --tagger particlenetDDT --migmat --n2cut n2_0p2 --skipmunfold --coffea_hists coffea_hists_withN2 --n2gen ../rhalph/UnfoldingParticleNet_N2Cut_18-09-24/FullRunII/ # ../python/unfolding_plotting.py
ls /data/dust/user/hinzmann/jetmass/JetMass/rhalph/UnfoldingParticleNet_N2Cut_18-09-24/FullRunII/prob*.pdf

# unfolded distributions
python plots_april_2024.py # ../python/pretty_postfit.py /data/dust/user/hinzmann/jetmass/JetMass/rhalph/UnfoldingParticleNet_N2Cut_18-09-24/FullRunII/ --mctruth --year RunII --data --coffea_hists /data/dust/user/hinzmann/jetmass/JetMass/python/coffea_hists_withN2 --n2gen
ls /data/dust/user/hinzmann/jetmass/JetMass/rhalph/UnfoldingParticleNet_N2Cut_18-09-24/FullRunII/plots/pretty_unfold_sigma/m*.pdf

# correlation matrix plot
python UnfoldingCorrelationMatrix.py
ls -lh UnfoldingParticleNet_N2Cut_18-09-24/FullRunII/corr*.pdf

# unfolded distributions with Pythia mass samples
python make_w_fit.py
ls /afs/desy.de/user/h/hinzmann/wjetmass/w_mass_d02-x01-y01-0Data.pdf

# print impact table
python print_impact_table.py
