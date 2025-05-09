import os

def exec_cmd(cmd, debug=False):
    print(cmd)
    if not debug:
        os.system(cmd)

for tagger in ["--particlenet"]:#, ""]:
    for name, args in [
        #("07-08-23",""),
        #("07-08-23Asimov","--prefitAsimov"),
        #("07-08-23Pseudo","--prefitAsimov --splitPseudo"),
        #("N2Cut_02-04-24","--n2gen"),
        #("N2Cut_02-04-24Asimov","--prefitAsimov --n2gen"),
        #("N2Cut_02-04-24Pseudo","--prefitAsimov --splitPseudo --n2gen"),

        #("18-09-24",""),
        ("N2Cut_18-09-24","--n2gen"),
        #("N2Cut_18-09-24Asimov","--prefitAsimov --n2gen"),
        #("18-09-24NoSys",""),
        #("N2Cut_18-09-24NoSys","--n2gen"),
        #("N2Cut_18-09-24AsimovNoSys","--prefitAsimov --n2gen"),
        #("18-09-24NoMatching",""),
        #("N2Cut_18-09-24NoMatching","--n2gen"),
        #("N2Cut_18-09-24AsimovNoReg","--prefitAsimov --n2gen"),
        #("N2Cut_18-09-24-UL18","--n2gen"),
        #("N2Cut_18-09-24-UL17","--n2gen"),
        #("N2Cut_18-09-24-UL16preVFP","--n2gen"),
        #("N2Cut_18-09-24-UL16postVFP","--n2gen"),
        #("N2Cut_18-09-24Asimov-UL18","--prefitAsimov --n2gen"),
        #("N2Cut_18-09-24Asimov-UL17","--prefitAsimov --n2gen"),
        #("N2Cut_18-09-24NoSys-UL18","--n2gen"),
        #("N2Cut_18-09-24NoSys-UL17","--n2gen"),
    ]:
#        exec_cmd("./unfolding_fit.py --TaggingEff --nonuniform --name {} {} {}".format(name, args, tagger), debug=False)
        exec_cmd("./unfolding_fit.py --TaggingEff --nonuniform --justplots --sumgenbins --name {} {} {}".format(name, args, tagger), debug=False)
#        exec_cmd("./unfolding_fit.py --impacts fits --TaggingEff --nonuniform --name {} {} {}".format(name, args, tagger), debug=False)
#        exec_cmd("./unfolding_fit.py --impacts plots --TaggingEff --nonuniform --name {} {} {}".format(name, args, tagger), debug=False)
#        exec_cmd("./unfolding_toys_closure.py -d /data/dust/user/hinzmann/jetmass/JetMass/rhalph/Unfolding"+("ParticleNet" if "particlenet" in tagger else "Substructure")+"_"+name+"/FullRunII --debug -s", debug=False)
#        exec_cmd("./unfolding_toys_closure.py -d /data/dust/user/hinzmann/jetmass/JetMass/rhalph/Unfolding"+("ParticleNet" if "particlenet" in tagger else "Substructure")+"_"+name+"/FullRunII --debug -p", debug=False)
