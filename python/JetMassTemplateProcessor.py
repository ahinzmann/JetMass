#!/usr/bin/env python
###!/usr/bin/env pythonJMS.sh
import awkward as ak
import numpy as np
from coffea import processor
from coffea.nanoevents import BaseSchema
from coffea.analysis_tools import PackedSelection
import coffea.lookup_tools
import correctionlib
import hist
from coffea.util import save
import os
import glob
from coffea_util import CoffeaWorkflow
from utils import jms_correction_files
from copy import deepcopy
withN2=False

jetmass_path = "/data/dust/user/hinzmann/jetmass"
ddtmaps_n2_path = f"{jetmass_path}/ddtmaps/ddtmaps_n2.npy"
ddtmaps_particlenet_path = f"{jetmass_path}/ddtmaps/ddtmaps_particlenet.npy"
kfactor_path = f"{jetmass_path}/NLOWeights"

JECsources = ["AbsoluteStat", "AbsoluteScale", "AbsoluteMPFBias", "Fragmentation",
"SinglePionECAL", "SinglePionHCAL", "FlavorQCD", "TimePtEta",
"RelativePtBB","RelativePtEC1", "RelativePtEC2", "RelativePtHF", "RelativeBal", "RelativeFSR", "RelativeSample",
"RelativeStatFSR", "RelativeStatEC", "RelativeStatHF", "RelativeJEREC1", "RelativeJEREC2", "RelativeJERHF",
"PileUpDataMC", "PileUpPtRef", "PileUpPtBB", "PileUpPtEC1", "PileUpPtEC2", "PileUpPtHF",
"Total",
  ]

if True:
  cset={}
  sfs={}
  for year in ["UL16preVFP","UL16postVFP","UL17","UL18"]:
    cset[year]=correctionlib.CorrectionSet.from_file("jet_jerc_"+year+".json")
    if year=="UL16preVFP":
      yearset="Summer19UL16APV_V7_MC"
    if year=="UL16postVFP":
      yearset="Summer19UL16_V7_MC"
    if year=="UL17":
      yearset="Summer19UL17_V5_MC"
    if year=="UL18":
      yearset="Summer19UL18_V5_MC"
    for source in JECsources:
      print(yearset+"_"+source+"_"+"AK4PFchs")
      sfs[source+year]=cset[year][yearset+"_"+source+"_"+"AK4PFchs"]

class JMSTemplates(processor.ProcessorABC):
    def __init__(
            self,
            year: str = "2017",
            jec: str = "nominal",
            variation_weight: str = "nominal",
            trigger_sf_var: str = "nominal",
            tagger: str = "substructure",
            gen_sort: str = "pt",
    ):
        self._year = year
        self._jec = jec
        self._variation_weight = variation_weight
        self._trigger_sf_variation = trigger_sf_var
        self._tagger_approach = tagger
        self._gen_sort = gen_sort
        tagger_approaches = ["substructure", "particlenet", "particlenetDDT"]
        if self._tagger_approach not in tagger_approaches:
            raise NotImplementedError(
                "You chose a tagger ({}) approach that is not implemented. Choose among:".format(self._tagger_approach),
                tagger_approaches
            )

        dataset_ax = hist.axis.StrCategory([], name="dataset", growth=True)
        # fakes_ax = hist.axis.StrCategory([], name="fakes", growth=True)
        fakes_ax = hist.axis.Boolean(name="fakes")
        # shift_ax = hist.axis.StrCategory([], name="shift", growth=True)
        jec_applied_ax = hist.axis.StrCategory(
            [], name="jecAppliedOn", label="JEC applied on", growth=True
        )
        # jec_ax = hist.axis.StrCategory(
        #     ["raw", "pt", "pt_up", "pt_down","pt_","pt_mJ_up", "down"], name="JEC", label="JEC"
        # )
        mJ_ax = hist.axis.Regular(50, 0.0, 500.0, name="mJ", label=r"$m_{SD}$ [GeV]")
        pT_ax = hist.axis.Regular(300, 0.0, 3000.0, name="pt", label=r"$p_{T}$ [GeV]")
        eta_ax = hist.axis.Regular(100, -6.5, 6.5, name="eta", label=r"$\eta$")
        eta_regions_ax = hist.axis.Variable([0, 1.3, 2.5], name="abs_eta_regions", label=r"$|\eta|$")
        phi_ax = hist.axis.Regular(100, -4, 4, name="phi", label=r"$\Phi$")
        phieta_ax = hist.axis.Regular(10000, -350, 350, name="phieta", label=r"$\Phi$ + 100 $\eta$")

        chf_ax = hist.axis.Regular(51, 0, 1.02, name="chf", label="CHF")
        nhf_ax = hist.axis.Regular(51, 0, 1.02, name="nhf", label="NHF")

        mJ_fit_ax = hist.axis.Regular(
            500, 0.0, 500.0, name="mJ", label=r"$m_{SD}$ [GeV]"
        )

        mPnet_fit_ax = hist.axis.Regular(
            500, 0.0, 500.0, name="mPnet", label=r"$m_{\mathrm{ParticleNet}}$ [GeV]"
        )

        rho_ax = hist.axis.Regular(100, -10.0, 0, name="rho", label=r"$\rho$")

        self._unfolding_ax = {
            "vjets": {
                "ptgen": hist.axis.Variable(
                    np.array([0, 650, 800, 1200, np.inf]),
                    name="ptgen",
                    label=r"$p_{T,\mathrm{gen}}$ [GeV]",
                ),
                "mJgen": hist.axis.Variable(
                    np.array([0.0, 70., 80, 90, np.inf]),
                    name="mJgen",
                    label=r"$m_{SD,\mathrm{gen}}$ [GeV]",
                ),
                "ptreco": hist.axis.Variable(
                    np.array([500, 575, 650, 725, 800, 1000, 1200, np.inf]),
                    name="ptreco",
                    label=r"$p_{T,\mathrm{reco}}$ [GeV]",
                ),
                "mJreco": hist.axis.Regular(
                    500,
                    0.0,
                    500.0,
                    name="mJreco",
                    label=r"$m_{SD,\mathrm{reco}}$ [GeV]",
                ),
            },
            "ttbar": {
                "ptgen": hist.axis.Variable(
                    np.array([0, 250, 400, 650, np.inf]),
                    name="ptgen",
                    label=r"$p_{T,\mathrm{gen}}$ [GeV]",
                ),
                "mJgen": hist.axis.Variable(
                    np.array(
                        [0, 55, 80, 87.5,  np.inf]
                    ),
                    name="mJgen",
                    label=r"$m_{SD,\mathrm{gen}}$ [GeV]",
                ),
                "ptreco": hist.axis.Variable(
                    np.array([200, 300, 400, 500, 650, np.inf]),
                    name="ptreco",
                    label=r"$p_{T,\mathrm{reco}}$ [GeV]",
                ),
                "mJreco": hist.axis.Regular(
                    500, 0, 500, name="mJreco", label=r"$m_{SD,\mathrm{reco}}$ [GeV]"
                ),
            },
        }

        self._pT_fit_ax = {
            "vjets": hist.axis.Variable(
                np.array([500, 650, 800, 1200, np.inf]),
                name="pt",
                label=r"$p_{T}$ [GeV]",
            ),
            "ttbar": hist.axis.Variable(
                np.array([200, 300, 400, 500, 650, np.inf]),
                name="pt",
                label=r"$p_{T}$ [GeV]",
            ),
        }

        hists = {}

        # create dense_lookup from custom n2ddt map
        corrected_str = {
            "none": "",
            "pt": "_corrected_pt",
            "pt&mJ": "_corrected_pt_mass",
        }

        n2ddtmap = np.load(ddtmaps_n2_path, allow_pickle=True).item()
        self._n2ddtmaps = {
            jec_applied_on: coffea.lookup_tools.dense_lookup.dense_lookup(
                n2ddtmap[
                    f"discddt_map_{year}_smooth_4_0p05{corrected_str[jec_applied_on]}"
                ][0],
                dims=(
                    n2ddtmap[
                        f"discddt_map_{year}_smooth_4_0p05{corrected_str[jec_applied_on]}"
                    ][1],
                    n2ddtmap[
                        f"discddt_map_{year}_smooth_4_0p05{corrected_str[jec_applied_on]}"
                    ][2],
                ),
            )
            for jec_applied_on in ["none", "pt", "pt&mJ"]
        }
        particlenetddtmap = np.load(ddtmaps_particlenet_path, allow_pickle=True).item()
        self._pNetMDWvsQCDddtmaps = {
            jec_applied_on: coffea.lookup_tools.dense_lookup.dense_lookup(
                particlenetddtmap[
                    f"discddt_map_{year}_smooth_4_0p975{corrected_str[jec_applied_on]}"
                ][0],
                dims=(
                    particlenetddtmap[
                        f"discddt_map_{year}_smooth_4_0p975{corrected_str[jec_applied_on]}"
                    ][1],
                    particlenetddtmap[
                        f"discddt_map_{year}_smooth_4_0p975{corrected_str[jec_applied_on]}"
                    ][2],
                ),
            )
            for jec_applied_on in ["none", "pt", "pt&mJ"]
        }

        self.trigger_scalefactors = correctionlib.CorrectionSet.from_file(
            "/data/dust/user/hinzmann/jetmass/JetMassNotebooks/data/"
            + "HLT_AK8PFJet_MC_trigger_sf_c2e731345f.json"
        )

        self.mjet_reco_correction = correctionlib.CorrectionSet.from_file(
            "/data/dust/user/hinzmann/jetmass/JetMass/python/"
            + jms_correction_files["notagger"]
        )

        # get some corrections and pack them into dense_lookups
        corrections_extractor = coffea.lookup_tools.extractor()
        for boson in ["W", "Z"]:
            fname = f"{kfactor_path}/{boson}JetsCorr.root"
            corrections_extractor.import_file(fname)
            corrections_extractor.add_weight_sets(
                [
                    f"{boson}_kfactor kfactor {fname}",
                    f"{boson}_ewcorr ewcorr {fname}",
                ]
            )

        corrections_extractor.finalize()

        self.corrections = corrections_extractor.make_evaluator()

        self._vjets_corrections = correctionlib.CorrectionSet.from_file(
            "/data/dust/user/hinzmann/jetmass/JetMass/python/"
            "ULvjets_corrections.json"
        )

        self._selections = ["vjets", "ttbar"]

        # these are selections that are linked as one specifies later in self._regions!
        self._cuts = {"vjets": ["n2ddt", "rhocut"], "ttbar": ["tau32", "tau21"]}

        # these are sample specific matching criteria
        # these are handled via 'any' of PackedSelection, so in case of multiple requirements,
        # be aware, that they are linked with OR!!
        self._matching_mappings = {
            "vjets_WJetsMatched": {"IsMergedWZ": 1},
            "vjets_WJetsUnmatched": {"IsMergedWZ": 0},
            "vjets_ZJetsMatched": {"IsMergedWZ": 1},
            "vjets_ZJetsUnmatched": {"IsMergedWZ": 0},
            "ttbar_TTToSemiLeptonic_mergedTop": {"IsMergedTop": 1},
            "ttbar_TTToSemiLeptonic_mergedW": {"IsMergedWZ": 1},
            "ttbar_TTToSemiLeptonic_mergedQB": {"IsMergedQB": 1},
            "ttbar_TTToSemiLeptonic_semiMergedTop": {"IsMergedWZ": 1, "IsMergedQB": 1},
            "ttbar_TTToSemiLeptonic_notMerged": {"IsNotMerged": 1},
        }

        # common control-plots
        hists.update(
            {
                "pt": hist.Hist(pT_ax, dataset_ax, jec_applied_ax, storage=hist.storage.Weight()),
                "eta": hist.Hist(eta_ax, dataset_ax, storage=hist.storage.Weight()),
                "phi": hist.Hist(phi_ax, dataset_ax, storage=hist.storage.Weight()),
                "phieta": hist.Hist(phieta_ax, dataset_ax, storage=hist.storage.Weight()),
                "mjet": hist.Hist(mJ_ax, dataset_ax, jec_applied_ax, storage=hist.storage.Weight()),
                "rho": hist.Hist(rho_ax, dataset_ax, jec_applied_ax, storage=hist.storage.Weight()),
                "npv": hist.Hist(
                    dataset_ax,
                    hist.axis.Regular(80, 0, 80, name="npv", label=r"$N_{PV}$"),
                    storage=hist.storage.Weight(),
                ),
                "ntrueint": hist.Hist(
                    dataset_ax,
                    hist.axis.Regular(80, 0, 80, name="ntrueint", label=r"$N_{TrueInt}$"),
                    storage=hist.storage.Weight(),
                ),
                "chf": hist.Hist(
                    dataset_ax,
                    chf_ax,
                    storage=hist.storage.Weight(),
                ),
                "nhf": hist.Hist(
                    dataset_ax,
                    nhf_ax,
                    storage=hist.storage.Weight(),
                ),
                "n2": hist.Hist(
                    dataset_ax,
                    hist.axis.Regular(51, -2, 2, name="n2", label="$N_{2}$"),
                    storage=hist.storage.Weight(),
                ),
                "n2ddt": hist.Hist(
                    dataset_ax,
                    jec_applied_ax,
                    hist.axis.Regular(51, -2, 2, name="n2ddt", label=r"$N_{2}^{\mathrm{DDT}}$"),
                    storage=hist.storage.Weight(),
                ),
                "tau21": hist.Hist(
                    dataset_ax,
                    hist.axis.Regular(51, 0, 1, name="tau21", label=r"$\frac{\tau_{2}}{\tau_{1}}$"),
                    storage=hist.storage.Weight(),
                ),
                "tau32": hist.Hist(
                    dataset_ax,
                    hist.axis.Regular(51, 0, 1, name="tau32", label=r"$\frac{\tau_{3}}{\tau_{2}}$"),
                    storage=hist.storage.Weight(),
                ),
                "pNet_TvsQCD": hist.Hist(
                    dataset_ax,
                    hist.axis.Regular(51, 0, 1, name="pNet_TvsQCD", label=r"pNet TvsQCD"),
                    storage=hist.storage.Weight(),
                ),
                "pNet_WvsQCD": hist.Hist(
                    dataset_ax,
                    hist.axis.Regular(51, 0, 1, name="pNet_WvsQCD", label=r"pNet WvsQCD"),
                    storage=hist.storage.Weight(),
                ),
                "pNet_MD_WvsQCD": hist.Hist(
                    dataset_ax,
                    hist.axis.Regular(51, 0, 1, name="pNet_MD_WvsQCD", label=r"pNet MD WvsQCD"),
                    storage=hist.storage.Weight(),
                ),
            }
        )

        # define regions in terms of selection-bits
        # for "old" approach using energy correlation and n-subjettiness substructure variables
        # new approach using particlenet (working points from https://indico.cern.ch/event/1152827/contributions/
        # 4840404/attachments/2428856/4162159/ParticleNet_SFs_ULNanoV9_JMAR_25April2022_PK.pdf
        tagger = {
            "vjets": {
                # "substructure": {"pass": {"n2": True}, "fail": {"n2": False}},
                "substructure": {"pass": {"n2ddt": True}, "fail": {"n2ddt": False}},
                "particlenet": {"pass": {"particlenetMDWvsQCD": True}, "fail": {"particlenetMDWvsQCD": False}},
                "particlenetDDT": {
                    "pass": {"particlenetMDWvsQCD_DDT": True},
                    "fail": {"particlenetMDWvsQCD_DDT": False}
                },
            },
            "ttbar": {
                "substructure": {
                    "pass": {"tau32": True},
                    "passW": {"tau32": False, "tau21": True},
                    "fail": {"tau32": False, "tau21": False},
                },
                "particlenet": {
                    "pass": {"particlenetTvsQCD": True},
                    "passW": {"particlenetTvsQCD": False, "particlenetWvsQCD": True},
                    "fail": {"particlenetTvsQCD": False, "particlenetWvsQCD": False},
                },
                "particlenetDDT": {
                    "pass": {"particlenetTvsQCD": True},
                    "passW": {"particlenetTvsQCD": False, "particlenetWvsQCD": True},
                    "fail": {"particlenetTvsQCD": False, "particlenetWvsQCD": False},
                },
            },
        }

        self._regions = {
            "vjets": {
                "inclusive": {"rhocut": True, "pt500cut": True, "trigger": True},
                "pass": {
                    **tagger["vjets"][self._tagger_approach]["pass"],
                    "rhocut": True, "pt500cut": True, "trigger": True
                },
                "fail": {
                    **tagger["vjets"][self._tagger_approach]["fail"],
                    "rhocut": True, "pt500cut": True, "trigger": True
                },
                # "inclusive_trigger": {
                #     "rhocut": True,
                #     "pt500cut": True,
                #     "trigger": True,
                # },
                # "pass_trigger": {
                #     **tagger["vjets"][self._tagger_approach]["pass"],
                #     "rhocut": True,
                #     "pt500cut": True,
                #     "trigger": True,
                # },
                # "fail_trigger": {
                #     **tagger["vjets"][self._tagger_approach]["fail"],
                #     "rhocut": True,
                #     "pt500cut": True,
                #     "trigger": True,
                # },
            },
            "ttbar": {
                "inclusive": {"pt200cut": True},
                "pass": {
                    **tagger["ttbar"][self._tagger_approach]["pass"],
                    "pt200cut": True
                },
                "passW": {
                    **tagger["ttbar"][self._tagger_approach]["passW"],
                    "pt200cut": True
                },
                "fail": {
                    **tagger["ttbar"][self._tagger_approach]["fail"],
                    "pt200cut": True
                },
            },
        }

        self._variations = [
            "0_0_all",
            "0_0_chargedH",
            "0_0_gamma",
            "0_0_neutralH",
            "0_0_other",
        ]
        for selection in self._selections:
            for region in self._regions[selection].keys():
                hists.update(
                    {
                        f"{selection}_mjet_{region}": hist.Hist(
                            mJ_fit_ax,
                            self._pT_fit_ax[selection],
                            dataset_ax,
                            jec_applied_ax,
                            eta_regions_ax,
                            storage=hist.storage.Weight(),
                        ),
                        f"{selection}_mPnet_{region}": hist.Hist(
                            mPnet_fit_ax,
                            self._pT_fit_ax[selection],
                            dataset_ax,
                            jec_applied_ax,
                            eta_regions_ax,
                            storage=hist.storage.Weight(),
                        ),
                        f"{selection}_pt_{region}": hist.Hist(
                            pT_ax,
                            dataset_ax,
                            jec_applied_ax,
                            storage=hist.storage.Weight(),
                        ),
                        f"{selection}_eta_{region}": hist.Hist(
                            eta_ax, dataset_ax, storage=hist.storage.Weight()
                        ),
                        f"{selection}_chf_{region}": hist.Hist(
                            dataset_ax,
                            chf_ax,
                            self._pT_fit_ax[selection],
                            storage=hist.storage.Weight(),
                        ),
                        f"{selection}_nhf_{region}": hist.Hist(
                            dataset_ax,
                            nhf_ax,
                            self._pT_fit_ax[selection],
                            storage=hist.storage.Weight(),
                        ),
                        f"{selection}_rho_{region}": hist.Hist(
                            rho_ax,
                            dataset_ax,
                            jec_applied_ax,
                            storage=hist.storage.Weight(),
                        ),
                        f"{selection}_mjet_v_jecfactor_{region}": hist.Hist(
                            mJ_ax,
                            eta_regions_ax,
                            hist.axis.Regular(
                                300, 0, 3, name="jecfactor", label="jecfactor",
                            ),
                            dataset_ax,
                            storage=hist.storage.Weight(),
                        ),
                    }
                )

                hists.update(
                    {
                        f"{selection}_mjet_unfolding_{region}": hist.Hist(
                            self._unfolding_ax[selection]["mJgen"],
                            self._unfolding_ax[selection]["ptgen"],
                            self._unfolding_ax[selection]["mJreco"],
                            self._unfolding_ax[selection]["ptreco"],
                            dataset_ax,
                            jec_applied_ax,
                            fakes_ax,
                            storage=hist.storage.Weight(),
                        ),
                    }
                )

                hists.update(
                    {
                        f"{selection}_mjetgen_unfolding_{region}": hist.Hist(
                            self._unfolding_ax[selection]["mJgen"],
                            self._unfolding_ax[selection]["ptgen"],
                            dataset_ax,
                            storage=hist.storage.Weight(),
                        ),
                    }
                )

                for variation in self._variations:
                    hists.update(
                        {
                            f"{selection}_mjet_{variation}_variation_{region}__up": hist.Hist(
                                mJ_fit_ax,
                                self._pT_fit_ax[selection],
                                eta_regions_ax,
                                dataset_ax,
                                jec_applied_ax,
                                storage=hist.storage.Weight(),
                            ),
                        }
                    )

                    hists.update(
                        {
                            f"{selection}_mjet_{variation}_variation_{region}__down": hist.Hist(
                                mJ_fit_ax,
                                self._pT_fit_ax[selection],
                                eta_regions_ax,
                                dataset_ax,
                                jec_applied_ax,
                                storage=hist.storage.Weight(),
                            ),
                        }
                    )
                    hists.update(
                        {
                            f"{selection}_mjet_unfolding_{variation}_variation_{region}__up": hist.Hist(
                                self._unfolding_ax[selection]["mJgen"],
                                self._unfolding_ax[selection]["ptgen"],
                                self._unfolding_ax[selection]["mJreco"],
                                self._unfolding_ax[selection]["ptreco"],
                                dataset_ax,
                                jec_applied_ax,
                                storage=hist.storage.Weight(),
                            ),
                        }
                    )
                    hists.update(
                        {
                            f"{selection}_mjet_unfolding_{variation}_variation_{region}__down": hist.Hist(
                                self._unfolding_ax[selection]["mJgen"],
                                self._unfolding_ax[selection]["ptgen"],
                                self._unfolding_ax[selection]["mJreco"],
                                self._unfolding_ax[selection]["ptreco"],
                                dataset_ax,
                                jec_applied_ax,
                                storage=hist.storage.Weight(),
                            ),
                        }
                    )

                hists.update(
                    {
                        f"{selection}_mPnet_0_0_all_variation_{region}__up": hist.Hist(
                            mPnet_fit_ax,
                            self._pT_fit_ax[selection],
                            eta_regions_ax,
                            dataset_ax,
                            jec_applied_ax,
                            storage=hist.storage.Weight(),
                        ),
                        f"{selection}_mPnet_0_0_all_variation_{region}__down": hist.Hist(
                            mPnet_fit_ax,
                            self._pT_fit_ax[selection],
                            eta_regions_ax,
                            dataset_ax,
                            jec_applied_ax,
                            storage=hist.storage.Weight(),
                        )
                    }
                )

        self._hists = lambda: {
            **hists,
            "nevents": processor.defaultdict_accumulator(float),
            "sumw": processor.defaultdict_accumulator(float),
            "sumw2": processor.defaultdict_accumulator(float),
        }

        self._triggerbits = [
            "HLT_PFJet320_v*",
            "HLT_PFJet400_v*",
            "HLT_PFJet450_v*",
            "HLT_PFJet500_v*",
            "HLT_PFJet550_v*",
            "HLT_AK8PFJet320_v*",
            "HLT_AK8PFJet400_v*",
            "HLT_AK8PFJet450_v*",
            "HLT_AK8PFJet500_v*",
            "HLT_AK8PFJet550_v*",
        ]

    def passes_trigger(self, events, trigger_name):
        return events["trigger_bits"][:, self._triggerbits.index(trigger_name)]

    @property
    def accumulator(self):
        return self._hists

    def n2ddt(self, pt, rho, n2, corrected="none"):
        quantile = self._n2ddtmaps[corrected](rho, pt)
        return n2 - quantile

    def pNetMDWvsQCDddt(self, pt, rho, val, corrected="none"):
        quantile = self._pNetMDWvsQCDddtmaps[corrected](rho, pt)
        return quantile - val

    def vjets_syst_weights(self, syst, vpt, boson="W"):
        evaluator = self._vjets_corrections[f"{boson}_FixedOrderComponent"]
        nominal = evaluator.evaluate("nominal", vpt)
        return evaluator.evaluate(syst, vpt)/nominal

    def vjets_syst_weights_envelope(self, systs, vpt, boson="W", edge="upper"):
        vals = np.array([self.vjets_syst_weights(f"{syst}", vpt, boson) for syst in systs])
        envelope_edge = np.max(vals, axis=0) if edge == "upper" else np.min(vals, axis=0)
        return envelope_edge

    def postprocess(self, accumulator):
        return accumulator

    def process(self, events):
        out = self.accumulator()

        dataset = events.metadata["dataset"]
        selection = events.metadata["selection"]

        isMC = "data" not in dataset.lower()

        # HEM15/16 Treatment
        # https://hypernews.cern.ch/HyperNews/CMS/get/JetMET/2000.html
        # courtesy of C.Matthies
        # https://github.com/MatthiesC/LegacyTopTagging/blob/master/include/Utils.h#L325-L328
        HEM_affected_lumi_fraction = 0.64844705699  # (Run 319077 (17.370008/pb) + Run C + Run D) / all 2018
        HEM_eta_min, HEM_eta_max = -3.2, -1.3
        HEM_phi_min, HEM_phi_max = -1.57, -0.87
        HEM_affected_event_jets = (
            (events.eta < HEM_eta_max)
            & (events.eta > HEM_eta_min)
            & (events.phi < HEM_phi_max)
            & (events.phi > HEM_phi_min)
        )
        treat_HEM = False
        event_weight_for_gen = deepcopy(events.weight)
        #print("weight", events.weight)
        #print("prefiringweight", events.prefiringweight)
        if isMC:
            if self._year == "UL18":
                events["weight"] = ak.where(
                    HEM_affected_event_jets, events.weight * (1 - HEM_affected_lumi_fraction), events.weight
                )
        else:
            if self._year == "UL18" and any(run in events.metadata["filename"] for run in ["RunC", "RunD"]):
                treat_HEM = True

        # evaluate matching criteria and created new masked events dataframe
        matching_mask = np.ones(len(events), dtype="bool")

        if dataset in self._matching_mappings.keys():

            matching_selection = PackedSelection()
            for branch_name, branch_value in self._matching_mappings[dataset].items():

                matching_selection.add(branch_name, events[branch_name] == branch_value)
            # BE AWARE OF THE FOLLOWING OR!!!!
            matching_mask = matching_selection.any(
                *self._matching_mappings[dataset].keys()
            )

        events = events[matching_mask]
        event_weight_for_gen = event_weight_for_gen[matching_mask]

        out["nevents"][dataset] = len(events)
        out["sumw"][dataset] = ak.sum(events.weight)
        out["sumw2"][dataset] = ak.sum(events.weight * events.weight)

        # right now its commented since i apply the kfactor when making the flat tree in UHH2
        # genpt = events.genjetpt
        # vpt = events.V_pt
        # if('WJets' in dataset):
        #     events.weight = events.weight/self.corrections['W_kfactor'](genpt)*self.corrections[f'W_ewcorr'](vpt)
        #     events.weight = events.weight*self.corrections['W_kfactor'](genpt)*self.corrections[f'W_ewcorr'](genpt)
        # if('ZJets' in dataset):
        #     events.weight = events.weight/self.corrections['Z_kfactor'](genpt)*self.corrections[f'Z_ewcorr'](vpt)
        #     events.weight = events.weight*self.corrections['Z_kfactor'](genpt)*self.corrections[f'Z_ewcorr'](genpt)

        jecfactors = {
            "nominal": events.jecfactor,
            "up": events.jecfactor_up,
            "down": events.jecfactor_down,
        }
        
        for s in JECsources:
         if s in self._jec:
          factors_up=[]
          factors_down=[]
          sf=sfs[s+self._year]
          #print([inp.name for inp in sf.inputs])
          for pt,eta,jec in zip(events.pt,events.eta,events.jecfactor):
            unc=sf.evaluate(eta,pt)
            #print(pt,eta,unc)
            factors_up+=[jec*(1.+unc)]
            factors_down+=[jec*(1.-unc)]
          jecfactors[s+"_up"]=np.array(factors_up)
          jecfactors[s+"_down"]=np.array(factors_down)
        
        #print(jecfactors["down"],jecfactors["Total_down"],jecfactors["up"],jecfactors["Total_up"])
       
        if "data" in dataset.lower():
            jecfactor = jecfactors["nominal"]
        else:
            jecfactor = jecfactors[self._jec]

        # apply top-pt reweighting weight
        events["weight"] = events.weight * events["toppt_weight"]
        if self._variation_weight != "nominal" and "data" not in dataset.lower() and len(events) > 0:
            variation_weights = {
                "toppt_off": 1. / events["toppt_weight"],
                "prefiring": 1. / (1.-(1.-events.prefiringweight)*0.2), # 20% of weight as uncertainty
                "pu_down": events["weight_pu_down"]/events["weight_pu"],
                "pu_up": events["weight_pu_up"]/events["weight_pu"],
            }
            if len(events["ps_weights"][0]) == 46:
                variation_weights["fsr_down"] = events["ps_weights"][:, 4] / events["ps_weights"][:, 0]
                variation_weights["fsr_up"] = events["ps_weights"][:, 5] / events["ps_weights"][:, 0]
                variation_weights["isr_down"] = events["ps_weights"][:, 26] / events["ps_weights"][:, 0]
                variation_weights["isr_up"] = events["ps_weights"][:, 27] / events["ps_weights"][:, 0]
                # for factor 4
                #variation_weights["fsr_down"] = events["ps_weights"][:, 6] / events["ps_weights"][:, 0]
                #variation_weights["fsr_up"] = events["ps_weights"][:, 7] / events["ps_weights"][:, 0]
                #variation_weights["isr_down"] = events["ps_weights"][:, 28] / events["ps_weights"][:, 0]
                #variation_weights["isr_up"] = events["ps_weights"][:, 29] / events["ps_weights"][:, 0]

            else:
                variation_weights["fsr_down"] = 1.0
                variation_weights["fsr_up"] = 1.0
                variation_weights["isr_down"] = 1.0
                variation_weights["isr_up"] = 1.0

            # not smoothed
            model_uncertainty_map={'Madgraph+Pythia': [[4248.748046875, 1950.68505859375, 3420.052001953125, 9013.298828125], [1137.9599609375, 566.2576904296875, 814.9030151367188, 2945.991943359375], [526.6923217773438, 263.8905944824219, 357.5408935546875, 1671.18603515625], [52.632930755615234, 26.49795913696289, 25.409000396728516, 212.7095947265625]], 'Madgraph+Herwig': [[4954.89111328125, 2149.37109375, 3797.093994140625, 5445.283203125], [1264.583984375, 499.2561950683594, 939.0938720703125, 1580.64404296875], [586.7092895507812, 273.48370361328125, 377.1571960449219, 829.7686157226562], [64.3490982055664, 30.3870792388916, 23.237180709838867, 82.36943054199219]], 'Pythia': [[1775.532958984375, 2102.533935546875, 4230.81396484375, 2258.155029296875], [387.2319030761719, 529.7987060546875, 978.967529296875, 578.1860961914062], [169.04600524902344, 262.5823974609375, 366.9169921875, 291.5531005859375], [12.388580322265625, 20.840530395507812, 26.876819610595703, 22.360410690307617]], 'Madgraph+Pythia_matched': [[431.5899963378906, 1160.4649658203125, 2545.98193359375, 2715.133056640625], [121.23719787597656, 338.66571044921875, 612.3568725585938, 942.3109130859375], [51.543968200683594, 162.98060607910156, 252.2751007080078, 559.7239990234375], [6.170756816864014, 18.149290084838867, 19.964210510253906, 83.4867172241211]], 'Madgraph+Herwig_matched': [[731.4122924804688, 1557.5, 3367.653076171875, 2267.81689453125], [187.9049072265625, 372.1142883300781, 831.7598876953125, 720.782470703125], [82.22386169433594, 203.77220153808594, 309.2331848144531, 345.2055969238281], [8.93737506866455, 21.44969940185547, 21.44969940185547, 41.25749969482422]], 'Pythia_matched': [[571.126220703125, 1746.572998046875, 3659.6650390625, 889.49560546875], [128.99139404296875, 444.3352966308594, 863.3652954101562, 198.31520080566406], [59.0753288269043, 224.03509521484375, 317.0176086425781, 94.38094329833984], [4.554941177368164, 17.485679626464844, 23.504680633544922, 6.6869049072265625]], 'Madgraph+Pythia_unmatched': [[3817.157958984375, 790.2199096679688, 874.069580078125, 6298.1650390625], [1016.7230224609375, 227.59210205078125, 202.54600524902344, 2003.6810302734375], [475.1482849121094, 100.91000366210938, 105.26589965820312, 1111.4620361328125], [46.4621696472168, 8.348671913146973, 5.444786071777344, 129.222900390625]], 'Madgraph+Herwig_unmatched': [[4223.47900390625, 591.8717041015625, 429.4410095214844, 3177.466064453125], [1076.678955078125, 127.14179992675781, 107.33399963378906, 859.8612060546875], [504.48541259765625, 69.71153259277344, 67.9240493774414, 484.56298828125], [55.4117317199707, 8.937376022338867, 1.7874749898910522, 41.11193084716797]], 'Pythia_unmatched': [[1204.406982421875, 355.96148681640625, 571.14892578125, 1368.6590576171875], [258.2405090332031, 85.46336364746094, 115.60220336914062, 379.87091064453125], [109.970703125, 38.54732894897461, 49.899478912353516, 197.1721954345703], [7.83364200592041, 3.354846954345703, 3.3721439838409424, 15.673500061035156]]}
            # smoothed 20.Nov 2025
            #model_uncertainty_map={'Madgraph+Pythia': [[4248.748046875, 1950.68505859375, 3420.052001953125, 9013.298828125], [1137.9599609375, 566.2576904296875, 814.9030151367188, 2945.991943359375], [526.6923217773438, 263.8905944824219, 357.5408935546875, 1671.18603515625], [52.632930755615234, 26.49795913696289, 25.409000396728516, 212.7095947265625]], 'Madgraph+Herwig': [[4954.89111328125, 2149.37109375, 3797.093994140625, 5445.283203125], [1264.583984375, 499.2561950683594, 939.0938720703125, 1580.64404296875], [586.7092895507812, 273.48370361328125, 377.1571960449219, 829.7686157226562], [64.3490982055664, 30.3870792388916, 23.237180709838867, 82.36943054199219]], 'Pythia': [[1775.532958984375, 2102.533935546875, 4230.81396484375, 2258.155029296875], [387.2319030761719, 529.7987060546875, 978.967529296875, 578.1860961914062], [169.04600524902344, 262.5823974609375, 366.9169921875, 291.5531005859375], [12.388580322265625, 20.840530395507812, 26.876819610595703, 22.360410690307617]], 'Madgraph+Pythia_matched': [[431.5899963378906, 1160.4649658203125, 2545.98193359375, 2715.133056640625], [121.23719787597656, 338.66571044921875, 612.3568725585938, 942.3109130859375], [51.543968200683594, 162.98060607910156, 252.2751007080078, 559.7239990234375], [6.170756816864014, 18.149290084838867, 19.964210510253906, 83.4867172241211]], 'Madgraph+Herwig_matched': [[727.716145157318, 1597.6894909720233, 3296.7794962470234, 2268.4859522806887], [182.4821188488741, 426.9495012570425, 731.7932229371237, 721.996877956913], [81.80892376734383, 209.02305326397172, 302.73418903935067, 345.30731240757234], [8.962098292832405, 21.146715534869546, 21.69681026055701, 41.25083708242983]], 'Pythia_matched': [[571.126220703125, 1746.572998046875, 3659.6650390625, 889.49560546875], [128.99139404296875, 444.3352966308594, 863.3652954101562, 198.31520080566406], [59.0753288269043, 224.03509521484375, 317.0176086425781, 94.38094329833984], [4.554941177368164, 17.485679626464844, 23.504680633544922, 6.6869049072265625]], 'Madgraph+Pythia_unmatched': [[3817.157958984375, 790.2199096679688, 874.069580078125, 6298.1650390625], [1016.7230224609375, 227.59210205078125, 202.54600524902344, 2003.6810302734375], [475.1482849121094, 100.91000366210938, 105.26589965820312, 1111.4620361328125], [46.4621696472168, 8.348671913146973, 5.444786071777344, 129.222900390625]], 'Madgraph+Herwig_unmatched': [[4325.077973005094, 519.1696940976591, 472.4635600019097, 3173.003616029336], [1059.8323721832212, 137.29987991046525, 100.33985071479405, 860.6467066867001], [501.21809961948185, 72.01694166208048, 66.0919814589597, 484.74620733368226], [60.0692956756437, 5.10148527401361, 2.413180677341756, 40.910186984796404]], 'Pythia_unmatched': [[1204.406982421875, 355.96148681640625, 571.14892578125, 1368.6590576171875], [258.2405090332031, 85.46336364746094, 115.60220336914062, 379.87091064453125], [109.970703125, 38.54732894897461, 49.899478912353516, 197.1721954345703], [7.83364200592041, 3.354846954345703, 3.3721439838409424, 15.673500061035156]]}
            matched_name=("_matched" if "WJetsMatched" in dataset else "_unmatched" if "WJetsUnmatched" in dataset else "")
            #print(dataset,matched_name)
            model_nominal=np.concatenate(model_uncertainty_map['Madgraph+Pythia'+matched_name])
            model_herwig=np.concatenate(model_uncertainty_map['Madgraph+Herwig'+matched_name])/model_nominal
            model_pythia=np.concatenate(model_uncertainty_map['Pythia'+matched_name])/model_nominal
            #print(model_nominal)
            def herwigWeight(pt,msd):
              ptmsd_bin =  4*(1*np.greater(pt,1200)  + 1*np.greater(pt,800)  + 1*np.greater(pt,650) ) + 1*np.greater(msd,90)  + 1*np.greater(msd,80)  + 1*np.greater(msd,70) 
              pt_bin =  1*np.greater(pt,1200)  + 1*np.greater(pt,800)  + 1*np.greater(pt,650)
              msd_bin =  1*np.greater(msd,90)  + 1*np.greater(msd,80)  + 1*np.greater(msd,70) 
              #print(pt,msd,ptmsd_bin,model_up/model_nominal)
              #if matched_name=="_matched":
                #weight=np.array(1.34802+-0.515421*np.tanh((1+0.880484)*(msd/80-1)))*np.equal(pt_bin,0)+\
                #(1.24764+-0.485236*np.tanh((1+0.257887)*(msd/80-1)))*np.equal(pt_bin,1)+\
                #(1.24957+-0.633737*np.tanh((1+0.478717)*(msd/80-1)))*np.equal(pt_bin,2)+\
                #(1.12929+-0.635186*np.tanh((1+0.459982)*(msd/80-1)))*np.equal(pt_bin,3)
#                weight=(np.minimum(0.748689+46.8516/np.minimum(msd,500),1.6946923732757568))*np.equal(pt_bin,0)+\
#(np.minimum(0.695131+41.5053/np.minimum(msd,500),1.5498948097229004))*np.equal(pt_bin,1)+\
#(np.minimum(0.513513+57.569/np.minimum(msd,500),1.5952179431915283))*np.equal(pt_bin,2)+\
#(np.minimum(0.385064+59.2418/np.minimum(msd,500),1.4483433961868286))*np.equal(pt_bin,3)
#                weight=(np.maximum(np.minimum(0.742892+47.2243/msd,1.6946923732757568),0.835250735282898))*np.equal(pt_bin,0)+\
#(np.maximum(np.minimum(0.69494+41.4956/msd,1.5498948097229004),0.7649093866348267))*np.equal(pt_bin,1)+\
#(np.maximum(np.minimum(0.513514+57.5534/msd,1.5952179431915283),0.6167425513267517))*np.equal(pt_bin,2)+\
#(np.maximum(np.minimum(0.271512+68.2576/msd,1.4483433961868286),0.4941803812980652))*np.equal(pt_bin,3)
                #weight=(1.72561+-0.0795648*pt_bin)*np.equal(msd_bin,0)+\
#(1.3655+-0.0953625*pt_bin)*np.equal(msd_bin,1)+\
#(1.34629+-0.0316384*pt_bin)*np.equal(msd_bin,2)+\
#(0.89504+-0.106615*pt_bin)*np.equal(msd_bin,3)
                #print(pt_bin,weight)
              #elif matched_name=="_unmatched":
                #weight=np.array(0.703326+-0.290031*np.tanh((1+2)*(msd/80-1)))*np.equal(pt_bin,0)+\
                #(0.635756+-0.265276*np.tanh((1+2)*(msd/80-1)))*np.equal(pt_bin,1)+\
                #(0.717737+-0.305687*np.tanh((1+1.99995)*(msd/80-1)))*np.equal(pt_bin,2)+\
                #(0.661489+-0.443594*np.tanh((1+2)*(msd/80-1)))*np.equal(pt_bin,3)
#                weight=(np.minimum(0.374434+26.111/msd,1.1064460277557373))*np.equal(pt_bin,0)+\
#(np.minimum(0.318753+25.7529/msd,1.0589697360992432))*np.equal(pt_bin,1)+\
#(np.minimum(0.34867+30.1493/msd,1.061743140220642))*np.equal(pt_bin,2)+\
#(np.minimum(0.169805+37.3865/msd,1.1926203966140747))*np.equal(pt_bin,3)
#                weight=(np.maximum(np.minimum(6.24169e-07+51.2385/msd,1.1064460277557373),0.5045066475868225))*np.equal(pt_bin,0)+\
#(np.maximum(np.minimum(5.22559e-08+47.1378/msd,1.0589697360992432),0.42914074659347534))*np.equal(pt_bin,1)+\
#(np.maximum(np.minimum(0.0223374+51.6595/msd,1.061743140220642),0.43596896529197693))*np.equal(pt_bin,2)+\
#(np.maximum(np.minimum(1.58409e-09+48.8641/msd,1.1926203966140747),0.3181474208831787))*np.equal(pt_bin,3)
                #weight=(1.11356+-0.0220099*pt_bin)*np.equal(msd_bin,0)+\
#(0.761545+-0.0688183*pt_bin)*np.equal(msd_bin,1)+\
#(0.468403+0.0468675*pt_bin)*np.equal(msd_bin,2)+\
#(0.524641+-0.0479194*pt_bin)*np.equal(msd_bin,3)
                #print(pt_bin,weight)
              #else:
                #weight=np.array(1.09448+-0.490705*np.tanh((1+-0.499977)*(msd/80-1)))*np.equal(pt_bin,0)+\
                #(1.00364+-0.466779*np.tanh((1+-0.499994)*(msd/80-1)))*np.equal(pt_bin,1)+\
                #(1.03367+-0.538012*np.tanh((1+-0.49998)*(msd/80-1)))*np.equal(pt_bin,2)+\
                #(1.0081+-0.620429*np.tanh((1+0.127099)*(msd/80-1)))*np.equal(pt_bin,3)
#                weight=(np.minimum(0.522507+46.2528/msd,1.1662002801895142))*np.equal(pt_bin,0)+\
#(np.minimum(0.47507+40.4676/msd,1.1112728118896484))*np.equal(pt_bin,1)+\
#(np.minimum(0.407146+50.5579/msd,1.1139507293701172))*np.equal(pt_bin,2)+\
#(np.minimum(0.273042+60.1531/msd,1.2226014137268066))*np.equal(pt_bin,3)
#                weight=(np.maximum(np.minimum(0.522451+46.2119/msd,1.1662002801895142),0.6041387319564819))*np.equal(pt_bin,0)+\
#(np.maximum(np.minimum(0.475244+40.446/msd,1.1112728118896484),0.5365405082702637))*np.equal(pt_bin,1)+\
#(np.maximum(np.minimum(0.411225+49.9662/msd,1.1139507293701172),0.49651479721069336))*np.equal(pt_bin,2)+\
#(np.maximum(np.minimum(0.338209+50/msd,1.2226014137268066),0.38723891973495483))*np.equal(pt_bin,3)
                #weight=(1.17565+-0.02724*pt_bin)*np.equal(msd_bin,0)+\
#(1.11622+-0.0773139*pt_bin)*np.equal(msd_bin,1)+\
#(1.12419+-0.0148967*pt_bin)*np.equal(msd_bin,2)+\
#(0.633854+-0.0605269*pt_bin)*np.equal(msd_bin,3)
              weight=np.take(model_herwig,ptmsd_bin,axis=0)
              #print("Herwig",weight,matched_name,msd,pt_bin,np.take(model_herwig,ptmsd_bin,axis=0))
              return weight
            def pythiaWeight(pt,msd):
              ptmsd_bin =  4*(np.trunc(pt/1200) % 2 + np.trunc(pt/800) % 2 + np.trunc(pt/650) % 2) + np.trunc(msd/90) % 2 + np.trunc(msd/80) % 2 + np.trunc(msd/70) % 2
              #print(pt,msd,ptmsd_bin,model_pythia/model_nominal)
              weight=np.take(model_pythia,ptmsd_bin,axis=0)
              #print("Pythia",weight,matched_name)
              return weight
            variation_weights["model_up"] = herwigWeight(events.pt_gen_ak8,events.msd_gen_ak8)
            #variation_weights["model_down"] = pythiaWeight(events.pt_gen_ak8,events.msd_gen_ak8)
            variation_weights["model_down"] = 1./((variation_weights["model_up"]-1.)/10.+1.) # inverse of herwig but scaled down by factor 10
            #print(variation_weights["model_up"])
            #print(variation_weights["model_down"])

            if ("WJets" in dataset or "ZJets" in dataset):
                boson = "W" if "W" in dataset else "Z"
                v_qcd_systs = [
                    f"{syst}_{direction}" for direction in ["up", "down"] for syst in ["d1K_NLO", "d2K_NLO", "d3K_NLO"]
                ]
                variation_weights["v_qcd_down"] = self.vjets_syst_weights_envelope(
                    v_qcd_systs,
                    events["V_pt"],
                    edge="lower",
                    boson=boson,
                )
                variation_weights["v_qcd_up"] = self.vjets_syst_weights_envelope(
                    v_qcd_systs,
                    events["V_pt"],
                    edge="upper",
                    boson=boson,
                )

                w_ewk_systs = [
                    f"{syst}_{direction}"
                    for direction in ["up", "down"]
                    for syst in ["d1kappa_EW", "W_d2kappa_EW", "W_d3kappa_EW"]
                ]
                z_ewk_systs = [
                    f"{syst}_{direction}"
                    for direction in ["up", "down"]
                    for syst in ["d1kappa_EW", "Z_d2kappa_EW", "Z_d3kappa_EW"]
                ]
                if boson == "W":
                    variation_weights["w_ewk_down"] = self.vjets_syst_weights_envelope(
                        w_ewk_systs,
                        events["V_pt"],
                        edge="lower",
                        boson=boson,
                    )
                    variation_weights["w_ewk_up"] = self.vjets_syst_weights_envelope(
                        w_ewk_systs,
                        events["V_pt"],
                        edge="upper",
                        boson=boson,
                    )
                    variation_weights["z_ewk_down"] = 1.0
                    variation_weights["z_ewk_up"] = 1.0
                else:
                    variation_weights["w_ewk_down"] = 1.0
                    variation_weights["w_ewk_up"] = 1.0
                    variation_weights["z_ewk_down"] = self.vjets_syst_weights_envelope(
                        z_ewk_systs,
                        events["V_pt"],
                        edge="lower",
                        boson=boson,
                    )
                    variation_weights["z_ewk_up"] = self.vjets_syst_weights_envelope(
                        z_ewk_systs,
                        events["V_pt"],
                        edge="upper",
                        boson=boson,
                    )
            else:
                variation_weights["v_qcd_down"] = 1.0
                variation_weights["v_qcd_up"] = 1.0
                variation_weights["w_ewk_down"] = 1.0
                variation_weights["w_ewk_up"] = 1.0
                variation_weights["z_ewk_down"] = 1.0
                variation_weights["z_ewk_up"] = 1.0

            events["weight"] = events.weight * variation_weights[self._variation_weight]
            event_weight_for_gen = event_weight_for_gen * variation_weights[self._variation_weight]
        pt_raw = events.pt
        pt = pt_raw * jecfactor

        ptgen_ = events.pt_gen_ak8

        mjet_raw = events.mjet
        mjet = mjet_raw * jecfactor

        mPnet_raw = events["ParticleNetMassRegression_mass"]
        mPnet = mPnet_raw * jecfactor

        mJgen_ = events.msd_gen_ak8

        # # not taking leading particle level jet but rather order by either dR(reco, gen) or N2(gen)
        # if "WJetsMatched" in dataset:
        #     if self._gen_sort == "n2":
        #         ptgen_ = ak.where(
        #             events.gentopjet_n2_0 < events.gentopjet_n2_1, events.gentopjet_pt_0, events.gentopjet_pt_1
        #         )
        #         mJgen_ = ak.where(
        #             events.gentopjet_n2_0 < events.gentopjet_n2_1, events.gentopjet_msd_0, events.gentopjet_msd_1
        #         )
        #     elif self._gen_sort == "dR":
        #         ptgen_ = ak.where(
        #             events.gentopjet_dR_reco_0 < events.gentopjet_dR_reco_1,
        #             events.gentopjet_pt_0,
        #             events.gentopjet_pt_1,
        #         )
        #         mJgen_ = ak.where(
        #             events.gentopjet_dR_reco_0 < events.gentopjet_dR_reco_1,
        #             events.gentopjet_msd_0,
        #             events.gentopjet_msd_1,
        #         )

        rho = 2 * np.log(mjet / pt)
        rho_raw = 2 * np.log(mjet_raw / pt_raw)
        rho_corrected_pt = 2 * np.log(mjet_raw / pt)
        rho_corrected_mJ = 2 * np.log(mjet / pt_raw)

        eta_ = events.eta
        phi_ = events.phi
        phieta_ = np.add(events.phi,np.floor(events.eta*100./7.)*7.)

        # apply trigger sf
        if isMC and selection == "vjets":
            trigger_sf_evaluator_450 = self.trigger_scalefactors[
                f"HLT_AK8PFJet450_triggersf_{self._year}"
            ]
            trigger_sf_evaluator_500 = self.trigger_scalefactors[
                f"HLT_AK8PFJet500_triggersf_{self._year}"
            ]
            first_ptbin = (pt < 650.0)
            events["weight"] = events.weight * ak.where(
                first_ptbin,
                trigger_sf_evaluator_450.evaluate(
                    pt, self._trigger_sf_variation
                ),
                trigger_sf_evaluator_500.evaluate(
                    pt, self._trigger_sf_variation
                )
            )

        events["ParticleNetMDDiscriminators_WvsQCD"] = (
            events["ParticleNetMD_probXqq"] + events["ParticleNetMD_probXcc"]
        ) / (events["ParticleNetMD_probXqq"] + events["ParticleNetMD_probXcc"] + events["ParticleNetMD_probQCD"])

        # apply trigger selection of vjets also to control plots
        m_cps = np.ones_like(events.pt, dtype=bool)
        vjets_trigger_mask = ak.where(
            pt < 650.0,
            events["trigger_bits"][:, self._triggerbits.index("HLT_AK8PFJet450_v*")] == 1,
            events["trigger_bits"][:, self._triggerbits.index("HLT_AK8PFJet500_v*")] == 1,
        )

        if selection == "vjets":
            m_cps = m_cps & vjets_trigger_mask

        out["pt"].fill(dataset=dataset, jecAppliedOn="pt", pt=pt[m_cps], weight=events.weight[m_cps])
        out["pt"].fill(dataset=dataset, jecAppliedOn="none", pt=pt_raw[m_cps], weight=events.weight[m_cps])
        out["eta"].fill(dataset=dataset, eta=eta_[m_cps], weight=events.weight[m_cps])
        out["phi"].fill(dataset=dataset, phi=phi_[m_cps], weight=events.weight[m_cps])
        out["phieta"].fill(dataset=dataset, phieta=phieta_[m_cps], weight=events.weight[m_cps])
        out["mjet"].fill(dataset=dataset, jecAppliedOn="mJ", mJ=mjet[m_cps], weight=events.weight[m_cps])
        out["mjet"].fill(dataset=dataset, jecAppliedOn="none", mJ=mjet_raw[m_cps], weight=events.weight[m_cps])
        out["rho"].fill(dataset=dataset, jecAppliedOn="pt&mJ", rho=rho[m_cps], weight=events.weight[m_cps])
        out["rho"].fill(
            dataset=dataset,
            jecAppliedOn="pt",
            rho=rho_corrected_pt[m_cps],
            weight=events.weight[m_cps],
        )
        out["rho"].fill(
            dataset=dataset,
            jecAppliedOn="mJ",
            rho=rho_corrected_mJ[m_cps],
            weight=events.weight[m_cps],
        )
        out["rho"].fill(dataset=dataset, jecAppliedOn="none", rho=rho_raw[m_cps], weight=events.weight[m_cps])

        out["npv"].fill(dataset=dataset, npv=events.n_pv[m_cps], weight=events.weight[m_cps])
        if isMC:
            out["ntrueint"].fill(dataset=dataset, ntrueint=events.n_trueint[m_cps], weight=events.weight[m_cps])
        out["chf"].fill(dataset=dataset, chf=events.CHF[m_cps], weight=events.weight[m_cps])
        out["nhf"].fill(dataset=dataset, nhf=events.NHF[m_cps], weight=events.weight[m_cps])

        out["n2"].fill(dataset=dataset, n2=events.N2[m_cps], weight=events.weight[m_cps])
        out["tau21"].fill(dataset=dataset, tau21=events.tau21[m_cps], weight=events.weight[m_cps])
        out["tau32"].fill(dataset=dataset, tau32=events.tau32[m_cps], weight=events.weight[m_cps])
        out["pNet_WvsQCD"].fill(
            dataset=dataset, pNet_WvsQCD=events["ParticleNetDiscriminators_WvsQCD"][m_cps], weight=events.weight[m_cps]
        )
        out["pNet_MD_WvsQCD"].fill(
            dataset=dataset,
            pNet_MD_WvsQCD=events["ParticleNetMDDiscriminators_WvsQCD"][m_cps],
            weight=events.weight[m_cps],
        )
        out["pNet_TvsQCD"].fill(
            dataset=dataset, pNet_TvsQCD=events["ParticleNetDiscriminators_TvsQCD"][m_cps], weight=events.weight[m_cps]
        )
        # for jec_applied_on in ['none','pt','pt&mJ']:
        for jec_applied_on in ["pt", "pt&mJ"]:
            selections = PackedSelection()
            pt_ = pt_raw
            if "pt" in jec_applied_on:
                pt_ = pt
            mJ_ = mjet_raw
            mPnet_ = mPnet_raw

            if "mJ" in jec_applied_on:
                mJ_ = mjet
                mPnet_ = mPnet

            rho_ = 2 * np.log(mJ_ / pt_)

            selections.add("pt500cut", (pt_ > 500))
            selections.add("pt200cut", (pt_ > 200))

            selections.add(
                "n2ddt",
                (
                    events.N2 > 0
                )
                # make sure to fail on events with default values for topjets
                # (do we need to remove those from fail region as well?)
                & (
                    self.n2ddt(pt_, rho_, events.N2, corrected=jec_applied_on) < 0
                ),  # actual N2-DDT tagger
            )
            out["n2ddt"].fill(
                dataset=dataset,
                jecAppliedOn=jec_applied_on,
                n2ddt=self.n2ddt(pt_, rho_, events.N2, corrected=jec_applied_on),
                weight=events.weight,
            )

            selections.add(
                "n2",
                (events.N2 > 0) & (events.N2 < 0.2)
            )

            # selections.add("rhocut",
            #                (rho_<-2.1)
            #                &(rho_>-6.0))
            selections.add("rhocut", rho_ < -2.1)
            # selections.add("rhocut", np.ones_like(events.pt, dtype=bool))

            selections.add("tau21", events.tau21 < 0.45)
            selections.add("tau32", events.tau32 < 0.5)

            selections.add("particlenetWvsQCD", events["ParticleNetMDDiscriminators_WvsQCD"] > 0.91)
            # selections.add("particlenetWvsQCD", events["ParticleNetDiscriminators_WvsQCD"] > 0.97)
            selections.add("particlenetTvsQCD", events["ParticleNetDiscriminators_TvsQCD"] > 0.96)
            selections.add("particlenetMDWvsQCD", events["ParticleNetMDDiscriminators_WvsQCD"] > 0.91)
            selections.add(
                "particlenetMDWvsQCD_DDT",
                (events["ParticleNetMDDiscriminators_WvsQCD"] > 0)
                & (
                    self.pNetMDWvsQCDddt(
                        pt_, rho_, events["ParticleNetMDDiscriminators_WvsQCD"], corrected=jec_applied_on
                    )
                    < 0
                ),
            )
            ###### WITHOUT N2 selection
            if not withN2:
              print("WITHOUT N2 SELECTION AT PARTICLE-LEVEL")
              selections.add(
                "gensel_drmatch",
                (events.pass_gen_selection == 1) & (events.dR_reco_gen < 0.4) & (mJgen_ > 30.),
              )

            if "n2_beta1_gen" not in events.fields:
                events.n2_beta1_gen = ak.ones_like(events.pt)

            ###### WITH N2 selection
            if withN2:
              print("WITH N2 SELECTION AT PARTICLE-LEVEL")
              selections.add(
                "gensel_drmatch",
                (events.pass_gen_selection == 1)
                & (events.dR_reco_gen < 0.4)
                & (mJgen_ > 30.)
                & (events.n2_beta1_gen < 0.2),
              )
            
            selections.add(
                "recosel",
                (events.pass_reco_selection == 1)
            )

            passing_hem_treatment = (
                ~HEM_affected_event_jets if treat_HEM else
                ak.ones_like(events.pt, dtype=bool)
            )

            selections.add("jetpfid",
                           (
                               (events.jetpfid == 1)
                               & (passing_hem_treatment == 1)
                           )
                           )
            selection = events.metadata["selection"]

            selections.add(
                "trigger",
                vjets_trigger_mask
            )

            for region in self._regions[selection].keys():
                smask_unfolding = selections.require(**self._regions[selection][region], recosel=True, jetpfid=True)
                selection_no_trigger = deepcopy(self._regions[selection][region])
                if "trigger" in selection_no_trigger:
                    selection_no_trigger.pop("trigger")
                smask_unfolding_gen = selections.require(**selection_no_trigger, recosel=True, jetpfid=True)
                corrector = self.mjet_reco_correction[
                    "response_g_" + ("jec" if "mJ" in jec_applied_on else "nojec") + f"_{self._year}"
                ]
                msd_correction = (
                    1.0/corrector.evaluate(pt_[smask_unfolding])  # divide since this is the response msdrec/mgen
                    if selection == "vjets"
                    else 1.0  # ak.ones_like(pt_[smask_unfolding])
                )

                # smask_unfolding_phasespace = selections.require(unfolding=True)
                out[f"{selection}_mjet_unfolding_{region}"].fill(
                    ptreco=pt_[smask_unfolding],
                    mJreco=mJ_[smask_unfolding] * msd_correction,
                    ptgen=ptgen_[smask_unfolding],
                    mJgen=mJgen_[smask_unfolding],
                    dataset=dataset,
                    fakes=selections.require(gensel_drmatch=False)[smask_unfolding]
                    if "WJetsMatched" in dataset
                    else np.zeros_like(smask_unfolding)[smask_unfolding],
                    jecAppliedOn=jec_applied_on,
                    weight=events.weight[smask_unfolding],
                )
                for split_size in [90.0, 80.0, 60.0]:
                    if "WJetsMatched" in dataset:
                        split_dataset = np.where(
                            np.random.rand(len(smask_unfolding[smask_unfolding])) < (split_size / 100.),
                            "vjets_WJetsMatched0p%i" % (split_size/10.),
                            "vjets_WJetsMatched0p%i" % (10 - (split_size/10.)),
                        )
                        out[f"{selection}_mjet_unfolding_{region}"].fill(
                            ptreco=pt_[smask_unfolding],
                            mJreco=mJ_[smask_unfolding] * msd_correction,
                            ptgen=ptgen_[smask_unfolding],
                            mJgen=mJgen_[smask_unfolding],
                            dataset=split_dataset,
                            fakes=selections.require(gensel_drmatch=False)[smask_unfolding],
                            jecAppliedOn=jec_applied_on,
                            weight=events.weight[smask_unfolding],
                        )

                # out[f"{selection}_mjet_unfolding_{region}"].fill(
                #     ptreco=pt_[smask_unfolding & smask_unfolding_phasespace],
                #     mJreco=mJ_[smask_unfolding & smask_unfolding_phasespace] * msd_correction,
                #     ptgen=ptgen_[smask_unfolding & smask_unfolding_phasespace],
                #     mJgen=mJgen_[smask_unfolding & smask_unfolding_phasespace],
                #     dataset=dataset,
                #     fakes="fakes",
                #     jecAppliedOn=jec_applied_on,
                #     weight=events.weight[smask_unfolding],
                # )

                out[f"{selection}_mjetgen_unfolding_{region}"].fill(
                    ptgen=ptgen_[smask_unfolding_gen],
                    mJgen=mJgen_[smask_unfolding_gen],
                    dataset=dataset,
                    weight=event_weight_for_gen[smask_unfolding_gen],
                )

                smask = selections.require(**self._regions[selection][region], jetpfid=True)

                out[f"{selection}_mjet_{region}"].fill(
                    dataset=dataset,
                    jecAppliedOn=jec_applied_on,
                    pt=pt_[smask],
                    abs_eta_regions=np.abs(eta_[smask]),
                    mJ=mJ_[smask],
                    weight=events.weight[smask],
                )

                out[f"{selection}_mPnet_{region}"].fill(
                    dataset=dataset,
                    jecAppliedOn=jec_applied_on,
                    pt=pt_[smask],
                    abs_eta_regions=np.abs(eta_[smask]),
                    mPnet=mPnet_[smask],
                    weight=events.weight[smask],
                )

                out[f"{selection}_pt_{region}"].fill(
                    dataset=dataset,
                    jecAppliedOn=jec_applied_on,
                    pt=pt_[smask],
                    weight=events.weight[smask],
                )

                out[f"{selection}_rho_{region}"].fill(
                    dataset=dataset,
                    jecAppliedOn=jec_applied_on,
                    rho=rho_[smask],
                    weight=events.weight[smask],
                )

                if jec_applied_on == "pt":
                    out[f"{selection}_mjet_v_jecfactor_{region}"].fill(
                        dataset=dataset,
                        mJ=mJ_[smask],
                        abs_eta_regions=np.abs(eta_[smask]),
                        jecfactor=jecfactor[smask],
                        weight=events.weight[smask]
                    )

                if jec_applied_on == "pt":
                    out[f"{selection}_chf_{region}"].fill(
                        dataset=dataset, chf=events.CHF[smask], pt=pt_[smask], weight=events.weight[smask]
                    )
                    out[f"{selection}_nhf_{region}"].fill(
                        dataset=dataset, nhf=events.NHF[smask], pt=pt_[smask], weight=events.weight[smask]
                    )
                    out[f"{selection}_eta_{region}"].fill(dataset=dataset, eta=eta_[smask], weight=events.weight[smask])

                if isMC:
                    for variation in self._variations:
                        mJVar_ = events[f"mjet_{variation}"]

                        if "mJ" in jec_applied_on:
                            mJVar_ = mJVar_ * jecfactor

                        out[f"{selection}_mjet_{variation}_variation_{region}__up"].fill(
                            dataset=dataset,
                            jecAppliedOn=jec_applied_on,
                            pt=pt_[smask],
                            mJ=mJVar_[:, 0][smask],
                            abs_eta_regions=np.abs(eta_[smask]),
                            weight=events.weight[smask],
                        )
                        out[f"{selection}_mjet_{variation}_variation_{region}__down"].fill(
                            dataset=dataset,
                            jecAppliedOn=jec_applied_on,
                            pt=pt_[smask],
                            mJ=mJVar_[:, 1][smask],
                            abs_eta_regions=np.abs(eta_[smask]),
                            weight=events.weight[smask],
                        )
                        # out[f"{selection}_mjet_unfolding_{variation}_variation_{region}__up"].fill(
                        #     ptreco=pt_[smask_unfolding],
                        #     mJreco=mJVar_[:, 0][smask_unfolding] * msd_correction,
                        #     ptgen=ptgen_[smask_unfolding],
                        #     mJgen=mJgen_[smask_unfolding],
                        #     dataset=dataset,
                        #     jecAppliedOn=jec_applied_on,
                        #     weight=events.weight[smask_unfolding],
                        # )
                        # out[f"{selection}_mjet_unfolding_{variation}_variation_{region}__down"].fill(
                        #     ptreco=pt_[smask_unfolding],
                        #     mJreco=mJVar_[:, 1][smask_unfolding] * msd_correction,
                        #     ptgen=ptgen_[smask_unfolding],
                        #     mJgen=mJgen_[smask_unfolding],
                        #     dataset=dataset,
                        #     jecAppliedOn=jec_applied_on,
                        #     weight=events.weight[smask_unfolding],
                        # )

                    out[f"{selection}_mPnet_0_0_all_variation_{region}__up"].fill(
                        dataset=dataset,
                        jecAppliedOn=jec_applied_on,
                        pt=pt_[smask],
                        mPnet=mPnet_[smask]*1.005,
                        abs_eta_regions=np.abs(eta_[smask]),
                        weight=events.weight[smask],
                    )
                    out[f"{selection}_mPnet_0_0_all_variation_{region}__down"].fill(
                        dataset=dataset,
                        jecAppliedOn=jec_applied_on,
                        pt=pt_[smask],
                        mPnet=mPnet_[smask]*0.995,
                        abs_eta_regions=np.abs(eta_[smask]),
                        weight=events.weight[smask],
                    )

        return out


if __name__ == "__main__":
    workflow = CoffeaWorkflow("JMSTemplates")

    workflow.parser.add_argument("--output", "-o", type=str, default="jms_templates.coffea")
    workflow.parser.add_argument("--year", default="UL17")
    workflow.parser.add_argument("--JEC", default="nominal")
    workflow.parser.add_argument("--variation", default="nominal", choices=[
        "isr_up", "isr_down",
        "fsr_up", "fsr_down",
        "model_up", "model_down",
        "pu_up", "pu_down",
        "toppt_off",
        "prefiring",
        "v_qcd_up", "v_qcd_down",
        "w_ewk_up", "w_ewk_down",
        "z_ewk_up", "z_ewk_down",
    ])
    workflow.parser.add_argument("--triggersf", default="nominal", choices=["nominal", "up", "down"])
    workflow.parser.add_argument("--maxfiles", type=int, default=-1)
    workflow.parser.add_argument(
        "--tagger", default="substructure", choices=["substructure", "particlenet", "particlenetDDT"]
    )

    workflow.parser.add_argument("--VJetsOnly", action="store_true")

    args = workflow.parse_args()

    if "withN2" in args.output:
      withN2=True
    else:
      withN2=False

    workflow.processor_instance = JMSTemplates(
        year=args.year,
        jec=args.JEC,
        variation_weight=args.variation,
        trigger_sf_var=args.triggersf,
        tagger=args.tagger
    )
    workflow.processor_schema = BaseSchema

    sample_pattern = (
        "/data/dust/user/hinzmann/jetmass/{SELECTION}Trees/workdir_{SELECTION}_{YEAR}/*{SAMPLE}*.root"
    )
    sample_names = {
        "vjets": [
            "Data",
            "WJets",
            "WJetsMatched",
            "WJetsUnmatched",
            "ZJets",
            "ZJetsMatched",
            "ZJetsUnmatched",
            "TTToHadronic",
            "TTToSemiLeptonic",
            "ST_tW_top",
            "ST_tW_antitop",
            "QCD",
        ],
        # "vjets":["Data.JetHT_RunB","Data.JetHT_RunC","Data.JetHT_RunD","Data.JetHT_RunE","Data.JetHT_RunF",],
        "ttbar": [
            "Data",
            "WJets",
            "DYJets",
            "TTToHadronic",
            "TTToSemiLeptonic",
            "TTToSemiLeptonic_mergedTop",
            "TTToSemiLeptonic_mergedW",
            "TTToSemiLeptonic_mergedQB",
            "TTToSemiLeptonic_semiMergedTop",
            "TTToSemiLeptonic_notMerged",
            "TTTo2L2Nu",
            "ST_t",
            "ST_tW",
            "ST_s",
            "QCD",
        ],
    }
    if args.VJetsOnly:
        sample_names = {
            "vjets": [
                "WJets",
                "WJetsMatched",
                "WJetsUnmatched",
                #"ZJets",
                #"ZJetsMatched",
                #"ZJetsUnmatched",
            ]
        }
    #sample_names = {
    #    "vjets": [
    #        "Data",
    #        "QCD",
    #    ],
    #}

    files = {}
    # for selection in ["vjets", "ttbar"]:
    for selection in sample_names.keys():
        def parent_samplename(s):
            return min(
                [
                    s.replace(child_samplename_suffix, "")
                    for child_samplename_suffix in [
                        "Matched",
                        "Unmatched",
                        "_mergedTop",
                        "_mergedW",
                        "_mergedQB",
                        "_semiMergedTop",
                        "notMerged",
                    ]
                ],
                key=len,
            )

        samples = {
            sample: glob.glob(
                sample_pattern.format(
                    SELECTION=selection,
                    YEAR=args.year,
                    SAMPLE=parent_samplename(sample),
                )
            )
            for sample in sample_names[selection]
        }

        for k, v in samples.items():
            if k not in files:
                files[f"{selection}_{k}"] = {
                    "files": [],
                    "treename": "AnalysisTree",
                    "metadata": {"selection": selection},
                }
            if args.maxfiles > 0:
                files[f"{selection}_{k}"]["files"] += v[: args.maxfiles]
            else:
                files[f"{selection}_{k}"]["files"] += v
            print(f"{selection}_{k}", len(files[f"{selection}_{k}"]["files"]))

    output_file_path = os.path.join(os.getcwd(), args.output)
    print("changing into /tmp dir:", os.environ["TMPDIR"])
    os.chdir(os.environ["TMPDIR"])
    if args.scaleout > 0:
        print("init dask client")
        # if(workflow.args.debug):
        #     workflow.init_dask_local_client()
        # else:
        # q = __import__("functools").partial(__import__("os")._exit, 0)  # FIXME
        # __import__("IPython").embed()  # FIXME
        workflow.processor_args["chunksize"] = 500000
        workflow.init_dask_htcondor_client(1, 2, 5)

    print("starting coffea runner")

    print(files)
    output = workflow.run(files)
    
    print("moving to output path:", output_file_path)

    if not output_file_path.endswith(".coffea"):
        output_file_path += ".coffea"

    save(output, output_file_path)
