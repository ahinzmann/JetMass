import hist
import numpy as np
import seaborn as sns
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt
import awkward as ak
import mplhep as hep
from collections.abc import Callable
from typing import Union

hep.style.use("CMS")

stability_color = "#1b9e77"
purity_color = "#d95f02"

label_tex_dict = {
    "pt": "p_{T}",
    "mjet": "m_{SD}",
}


lumi = 41.47968052876168  # fb^-1


def cms_label(ax, fs=20):
    hep.cms.label(label=", Work in Progress", year=2017, ax=ax, fontsize=fs)


def fax(w=9, h=9):
    return plt.subplots(figsize=(w, h))


def migration_metric(h: hist.Hist, axis_name: str = "pt_reco", flow: bool = False):
    axes = [a.name for a in h.axes]
    if axis_name not in axes:
        raise NameError(f"Did not find {axis_name} among axes of hist!")
    axis_index = axes.index(axis_name)
    mat = h.to_numpy(flow=flow)[0]
    if axis_index != 0:
        mat = mat.T
    metric_bin_contents = []
    metric_bin_edges = h.to_numpy(flow=flow)[axis_index + 1]
    other_dim_edges = h.to_numpy(flow=flow)[(1 - axis_index) + 1]
    main_dim_max_bin = len(metric_bin_edges) - 1 - (2 if flow else 0)  # -1 for last edge and -2 for uflow oflow
    second_dim_max_bin = len(other_dim_edges) - 1 - (2 if flow else 0)

    renormed_mat = mat / np.sum(mat, axis=1)[:, None]

    for bin_ind in range(main_dim_max_bin):
        bin_ind_x = bin_ind
        bin_ind_y = bin_ind
        bin_ind_y = bin_ind
        if flow:
            bin_ind_x = bin_ind + 1
            bin_ind_y = min(bin_ind + 1, second_dim_max_bin + 1)  # set to overflow of secondary dim if bin_ind exceeds
            if bin_ind_y != bin_ind + 1:
                print("Warning! reached end of binning in secondary dimension! taking counts from overflow for renorm")
        metric_bin_contents.append(renormed_mat[bin_ind_x, bin_ind_y])

    # return calculated metric and bin edges without flow
    return (
        np.array(metric_bin_contents),
        metric_bin_edges[1:-1] if flow else metric_bin_edges,
    )


class Unfolding1DPlotter(object):
    def __init__(self, variable: str = "mjet", reco_correction: Union[float, Callable] = 1.0, flow: bool = False):
        self.reco_correction = reco_correction
        self.variable = variable
        self.flow = flow

    def reco_corr_eval(self, events: ak.Array):
        if isinstance(self.reco_correction, Callable):
            return self.reco_correction(events["pt"])
        elif isinstance(self.reco_correction, float):
            return self.reco_correction
        else:
            raise TypeError("reco mass correction factors has to be either callable or float!")

    def build_migration_matrix(
        self,
        reco_bins: hist.axis,
        gen_bins: hist.axis,
        events: ak.Array,
    ) -> hist.Hist:
        h = hist.Hist(reco_bins, gen_bins, storage=hist.storage.Weight())
        h.fill(
            **{
                reco_bins.name: events[self.variable] * self.reco_corr_eval(events),
                gen_bins.name: events[f"{self.variable}gen"],
                "weight": events.weight,
            }
        )
        return h

    def plot_migration_metric(
        self, binning: np.ndarray, events: ak.Array, w: int = 9, h: int = 9, threshold: float = None
    ):
        f, ax = fax(w, h)

        migmat = self.build_migration_matrix(
            hist.axis.Variable(binning, name=f"{self.variable}_reco", overflow=self.flow),
            hist.axis.Variable(binning, name=f"{self.variable}_gen", overflow=self.flow),
            events,
        )

        hep.histplot(
            migration_metric(migmat, f"{self.variable}_reco", flow=self.flow),
            label="stability",
            ax=ax,
            **{"color": stability_color},
        )
        hep.histplot(
            migration_metric(migmat, f"{self.variable}_gen", flow=self.flow),
            label="purity",
            ax=ax,
            **{"color": purity_color},
        )
        if threshold is not None:
            ax.plot(ax.get_xlim(), [threshold, threshold], "k--", alpha=0.6)

        ax.legend()
        ax.set_xlabel(r"$%s~$[GeV]" % label_tex_dict[self.variable])
        ax.set_ylabel("binning metric")
        cms_label(ax)

        return f, ax

    def plot_migration_metric_nbins_comparison(
        self,
        xmin: float,
        xmax: float,
        events: ak.Array,
        nbins_list: list[int] = [100, 50],
        w: int = 12,
        h: int = 12,
    ):
        f, ax = fax(w, h)
        for nbins in nbins_list:
            migmat = self.build_migration_matrix(
                hist.axis.Regular(nbins, xmin, xmax, name=f"{self.variable}_reco", overflow=self.flow),
                hist.axis.Regular(nbins, xmin, xmax, name=f"{self.variable}_gen", overflow=self.flow),
                events,
            )
            hep.histplot(
                migration_metric(migmat, f"{self.variable}_reco", flow=self.flow),
                label=f"stability nbins={nbins}",
                ax=ax,
            )
            hep.histplot(
                migration_metric(migmat, f"{self.variable}_gen", flow=self.flow), label=f"purity nbins={nbins}", ax=ax
            )
        ax.legend()
        cms_label(ax, fs=25)
        ax.set_xlabel(r"$%s~$[GeV]" % label_tex_dict[self.variable])
        ax.set_ylabel("binning metric")

        return f, ax

    def plot_migration_matrix(
        self,
        reco_binning: np.ndarray,
        gen_binning: np.ndarray,
        events: ak.Array,
        w: int = 9,
        h: int = 9,
    ):
        migmat = self.build_migration_matrix(
            hist.axis.Variable(reco_binning, name=f"{self.variable}_reco", overflow=self.flow),
            hist.axis.Variable(gen_binning, name=f"{self.variable}_gen", overflow=self.flow),
            events,
        )

        f, ax = fax()
        hep.hist2dplot(migmat.to_numpy(), ax=ax)

        cms_label(ax)
        ax.set_xlabel(r"$%s^\mathrm{reco}}~$[GeV]" % label_tex_dict[self.variable])
        ax.set_ylabel(r"$%s^\mathrm{gen}}~$[GeV]" % label_tex_dict[self.variable])
        return f, ax

    def plot_distributions(
        self,
        reco_binning: np.ndarray,
        gen_binning: np.ndarray,
        events: ak.Array,
        w: int = 9,
        h: int = 9,
    ):
        f, ax = fax(w, h)

        migmat = self.build_migration_matrix(
            hist.axis.Variable(reco_binning, name=f"{self.variable}_reco", overflow=self.flow),
            hist.axis.Variable(gen_binning, name=f"{self.variable}_gen", overflow=self.flow),
            events,
        )

        hep.histplot(migmat[::sum, :], ax=ax, label=r"$%s^\mathrm{gen}}$" % label_tex_dict[self.variable])
        hep.histplot(migmat[:, ::sum], ax=ax, label=r"$%s^\mathrm{reco}}$" % label_tex_dict[self.variable])
        ax.legend()
        ax.set_xlabel(r"$%s~$[GeV]" % label_tex_dict[self.variable])
        cms_label(ax)
        return f, ax


def setup_edges(x: np.ndarray, y: np.ndarray, nth_subtick: int = 1):
    edges = x
    edges = np.array(
        list(map(lambda x: round(x, 2), list(edges[:-1:nth_subtick]) * len(y[:-2]) + list(edges[::nth_subtick]))),
        # -2: -1 to remove last y edge and -1 to remove last another one to add complete row of x edges
        dtype=str,
    )
    return edges


def plot_migration_matrix(h2d: hist.Hist, zlog: bool = False):
    gen_pt_edges = h2d[1]
    gen_pt_edges[-1] = 2 * gen_pt_edges[-2] - gen_pt_edges[-3]
    gen_msd_edges = h2d[2]
    gen_msd_edges[-1] = 2 * gen_msd_edges[-2] - gen_msd_edges[-3]

    reco_pt_edges = h2d[3]
    reco_pt_edges[-1] = 2 * reco_pt_edges[-2] - reco_pt_edges[-3]
    reco_msd_edges = h2d[4]

    edges_generator = setup_edges(gen_msd_edges, gen_pt_edges)
    edges_detector = setup_edges(reco_msd_edges, reco_pt_edges)

    x_shape = h2d[0].shape[0] * h2d[0].shape[1]
    y_shape = h2d[0].shape[2] * h2d[0].shape[3]
    mat = h2d[0].reshape((x_shape, y_shape)).T  # gen-bins on x-axis

    fig, (ax, cax) = plt.subplots(ncols=2, figsize=(12, 12), gridspec_kw={"width_ratios": [1, 0.02]})

    ax_pt_generator = ax.twiny()
    ax_pt_detector = ax.twinx()

    # colorbar
    n_tick_msd = 3
    every_nth_tick = int(len(gen_msd_edges) / n_tick_msd)
    generator_labels = setup_edges(gen_msd_edges, gen_pt_edges, every_nth_tick)
    msd_tick_position_generator = np.linspace(0, x_shape, len(generator_labels))
    n_tick_msd = 3
    every_nth_tick = int(len(reco_msd_edges) / n_tick_msd)
    detector_labels = setup_edges(reco_msd_edges, reco_pt_edges, every_nth_tick)
    msd_tick_position_detector = np.linspace(0, y_shape, len(detector_labels))

    sns.heatmap(mat, ax=ax, cmap="magma", norm=LogNorm() if zlog else None, cbar=False)

    fig.colorbar(ax.get_children()[0], cax=cax, orientation="vertical", label="Events")

    ax.invert_yaxis()
    ax_pt_detector.invert_yaxis()

    for i in range(1, len(reco_pt_edges) - 1):
        min_ = 0
        max_ = len(edges_generator)
        span = len(reco_msd_edges) - 1
        span_arr = [span * i, span * i]
        ax.plot([min_, max_], span_arr, "k--", alpha=0.6)
    for i in range(1, len(gen_pt_edges) - 1):
        min_ = 0
        max_ = len(edges_detector)
        span = len(gen_msd_edges) - 1
        span_arr = [span * i, span * i]
        ax.plot(span_arr, [min_, max_], "k--", alpha=0.6)

    generator_labels[-1] = r"$\infty$"
    ax.set_xticks(msd_tick_position_generator)
    ax.set_xticklabels(generator_labels)

    ax.set_yticks(msd_tick_position_detector)
    ax.set_yticklabels(detector_labels)

    pt_tick_position_generator = np.linspace(0, x_shape, len(gen_pt_edges))
    ax_pt_generator.set_xlim(ax.get_xlim())
    ax_pt_generator.set_xticks(pt_tick_position_generator)
    gen_pt_labels = gen_pt_edges.astype(dtype=str)
    gen_pt_labels[-1] = r"$\infty$"
    ax_pt_generator.set_xticklabels(gen_pt_labels)
    ax_pt_generator.set_xlabel("$p_{T,gen}$ [GeV]")

    pt_tick_position_detector = np.linspace(0, y_shape, len(reco_pt_edges))
    ax_pt_detector.set_ylim(ax.get_ylim())
    ax_pt_detector.set_yticks(pt_tick_position_detector)
    reco_pt_labels = reco_pt_edges.astype(dtype=str)
    reco_pt_labels[-1] = r"$\infty$"
    ax_pt_detector.set_yticklabels(reco_pt_labels)
    ax_pt_detector.set_ylabel("$p_{T,reco}$ [GeV]")

    ax.set_xlabel("$m_{SD,gen}$ [GeV]")
    ax.set_ylabel("$m_{SD,reco}$ [GeV]")

    hep.cms.text("Simulation, Work in progress", ax=ax, fontsize=23, pad=0.03)
    ax.text(0.05 * x_shape, 0.9 * y_shape, r"$W$(qq)+jets")
    fig.tight_layout()
    plt.savefig(
        "migration_matrix_final_binning.pdf",
        bbox_inches="tight",
        pad_inches=0.01,
    )
