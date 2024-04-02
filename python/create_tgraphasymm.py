import ROOT
import argparse
import numpy as np
import pickle

def dict_to_tga(H):
    edges = H["edges"]
    
    x = (edges[1:]+edges[:-1])/2.
    xl = x-edges[:-1]
    xh = edges[1:]-x

    y = H["values"]
    yl = np.sqrt(H["variances"][0])
    yh = np.sqrt(H["variances"][1])

    tga = ROOT.TGraphAsymmErrors(len(x), x, y, xl, xh, yl, yh)

    return tga

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--input",
        "-i",
        help="fit directory containing already extracted final unfolding histograms in numpy format.",
    )

    parser.add_argument(
        "--name",
        "-n",
        help="Name of the fit process.",
        default="CombinedFit"
    )

    args = parser.parse_args()

    hists = pickle.load(open("{}/m_unfold_hists.pkl".format(args.input),"rb"))


    tgraphs =  {
        k: dict_to_tga(v)
        for k, v in hists.items()
        if "munfold" in k 
    }

    fout = ROOT.TFile("{}/{}_results.root".format(args.input, args.name), "UPDATE")
    for k,v in tgraphs.items():
        v.SetNameTitle(k,k)
        v.Write()