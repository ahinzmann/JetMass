#!/usr/bin/env python3
import argparse
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--particlenet", action="store_true")
    parser.add_argument("--prefitAsimov", action="store_true")
    parser.add_argument("--splitPseudo", action="store_true")
    parser.add_argument("--name", default="")
    parser.add_argument("--impacts", choices=["none", "fits", "plots"], default="none")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--sumgenbins", action="store_true")
    parser.add_argument("--justplots", action="store_true", help="just redo the plots.")
    parser.add_argument("--nonuniform", action="store_true")
    parser.add_argument("--n2gen", action="store_true")
    
    args = parser.parse_args()

    cmd = "python jetmass_combination.py -M unfolding --year RunII --configs configs/unfolding/WJets*.py "

    regularization = "nonuniform" if args.nonuniform else "uniform"

    extra_options = ""
    if args.prefitAsimov:
        extra_options += " --prefitAsimov "
    if args.splitPseudo:
        extra_options += " --splitPseudo "
    if args.particlenet:
        extra_options += ' --tagger particlenetDDT '

    if len(extra_options) > 0:
        extra_options = r' --extra-options " {} "'.format(extra_options.replace('"', r'\"'))

    fit_name = ""
    if args.name != "":
        fit_name = "_{}".format(args.name)

    regularizations = {
        "uniform": {
            "particlenet": r'\"regularizationStrength\":0.85,\"regularization\": [\"pt\"]',
            "substructure": r'\"regularizationStrength\":0.9,\"regularization\": [\"pt\"]',
        },
        "nonuniform": {
            "particlenet": r'\"scaleGenBinWidth\":\"False\", \"uniformGenbins\":\"False\",\"regularizationStrength\":1.3,\"regularization\": [\"msd\",\"pt\"]', # noqa
            "substructure": r'\"scaleGenBinWidth\":\"False\", \"uniformGenbins\":\"False\",\"regularizationStrength\":1.45,\"regularization\": [\"msd\", \"pt\"]', # noqa
            # "particlenet": r'\"scaleGenBinWidth\":\"False\", \"uniformGenbins\":\"False\",\"regularizationStrength\":1.35,\"regularization\": [\"msd\",\"pt\"]', # noqa
            # "substructure": r'\"scaleGenBinWidth\":\"False\", \"uniformGenbins\":\"False\",\"regularizationStrength\":1.4,\"regularization\": [\"msd\", \"pt\"]', # noqa
            # "particlenet": r'\"scaleGenBinWidth\":\"True\", \"uniformGenbins\":\"False\",\"regularizationStrength\":0.000230,\"regularization\": [\"pt\"]', # noqa
            # "substructure": r'\"scaleGenBinWidth\":\"True\", \"uniformGenbins\":\"False\",\"regularizationStrength\":0.000415,\"regularization\": [\"pt\"]', # noqa
        }
    }
    if args.particlenet:
        cmd += " --workdir UnfoldingParticleNet{} ".format(fit_name)
        # cmd += r' --config-update "{\"regularizationStrength\":1.24}" '
        cmd += r' --config-update "{%s}"' % (regularizations[regularization]["particlenet"])
    else:
        cmd += " --workdir UnfoldingSubstructure{} ".format(fit_name)
        cmd += r' --config-update "{%s}"' % (regularizations[regularization]["substructure"])
        # cmd += r' --config-update "{\"regularizationStrength\":0.96,'
        # cmd += r' --config-update "{\"regularizationStrength\":1.08}" '

    cmd += extra_options
    if args.impacts != "none":
        cmd += " --impacts {} ".format(args.impacts)
    if args.justplots:
        cmd += " --justplots "
    if args.sumgenbins:
        cmd += " --sumgenbins "
    
    if args.n2gen:
        cmd += " --n2gen "

    print(cmd)
    if not args.debug:
        os.system(cmd)
