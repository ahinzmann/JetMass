import os

def exec_cmd(cmd, debug=False):
    print(cmd)
    if not debug:
        os.system(cmd)

for tagger in ["", "--particlenet"]:
    for name, args in [
        ("07-08-23",""),
        #("07-08-23Asimov","--prefitAsimov"),
        #("07-08-23Pseudo","--prefitAsimov --splitPseudo"),
        ("N2Cut_02-04-24","--n2gen"),
        #("N2Cut_02-04-24Asimov","--prefitAsimov --n2gen"),
        #("N2Cut_02-04-24Pseudo","--prefitAsimov --splitPseudo --n2gen"),
    ]:
        exec_cmd("./unfolding_fit.py --nonuniform --justplots --name {} {} {}".format(name, args, tagger), debug=False)
