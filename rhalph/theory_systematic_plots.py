import os

for unc in [#"CMS_lumi", # not a shape uncertainty
#"normUnc", # not a shape uncertainty
#"triggersf",
#"pu"
#"jec",
#"toppt",
#"tag_eff_sf", # not a shape uncertainty
#"isr",
#"fsr",
"v_qcd",
"w_ewk",
]:
  s="/data/dust/user/hinzmann/jetmass/JetMass/rhalph/../python/pretty_postfit.py /data/dust/user/hinzmann/jetmass/JetMass/rhalph/UnfoldingSubstructure_N2Cut_02-04-24/FullRunII/ --mctruth --year RunII --data --coffea_hists /data/dust/user/hinzmann/jetmass/JetMassFits/coffea_hists/msdgen30n2cut --n2gen --theory_uncertainty "+unc
  print(s)
  os.system(s)
