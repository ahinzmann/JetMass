#!/usr/bin/env pythonJMS.sh
import numpy as np
import uproot
from utils import numpy_to_th2, hist_to_th1
import pickle

def get_unfolding_hists(fit_dir):
    # TODO implement here after implementing in pretty_postfit
    #hists = np.load("{}/m_unfold_hists.npy".format(fit_dir), allow_pickle=True).item()
    hists = pickle.load(open("{}/m_unfold_hists.pkl".format(fit_dir),"rb"))

    return {
        k: hist_to_th1(v, k)
        for k, v in hists.items()
        if "munfold" not in k 
    }


def get_correlation_matrix(fit_dir):
    corr_mat_npy = np.load("{}/poi_correlation_matrix.npy".format(fit_dir), allow_pickle=True, encoding="bytes").item()
    edges = np.arange(0., len(corr_mat_npy[b"pois"])+1, dtype=float)
    print(edges)
    return numpy_to_th2(
        corr_mat_npy[b"covarianceMatrix"],
        edges,
        edges,
        "correlation_matrix",
        "pois",
        "pois"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "This script collects results (unfolding histograms and correlation matrix)"
            + " in numpy format and creates a ROOT file for further use in hepdata and possibly rivet."
        )
    )
    parser.add_argument(
        "--input",
        "-i",
        help="fit directory containing already extracted corr-matrix and final unfolding histograms in numpy format.",
    )
    parser.add_argument(
        "--name",
        "-n",
        help="Name of the fit process.",
        default="CombinedFit"
    )

    args = parser.parse_args()

    root_output = uproot.recreate("{}/{}_results.root".format(args.input, args.name))

    unfolding_hists = get_unfolding_hists(args.input)
    for title, th1 in unfolding_hists.items():
        root_output[title] = th1

    correlation_matrix = get_correlation_matrix(args.input)
    root_output["correlation_matrix"] = correlation_matrix
