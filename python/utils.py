import uproot
import numpy as np
import awkward as ak

jms_correction_files = {
    "n2ddt": "jms_corrections_n2ddt_quadratic_a99bef5742.json",
    "pNetddt": "jms_corrections_pNetddt_quadratic_f5f5ad1060.json",
    "notagger": "jms_corrections_notagger_quadratic_1efba6addc.json",

}
jms_correction_files["substructure"] = jms_correction_files["n2ddt"]
jms_correction_files["particlenetDDT"] = jms_correction_files["pNetddt"]

year_alias = {
    "UL16preVFP": "legacy 2016 (early)",
    "UL16postVFP": "legacy 2016 (late)",
    "UL17": "legacy 2017",
    "UL18": "legacy 2018",
}


def numpy_to_th2(
    H, x_edges, y_edges, hist_title="", x_title="", y_title="", add_empty_flow=True
):

    x_taxis = uproot.writing.identify.to_TAxis(
        x_title, x_title, len(x_edges[:-1]), x_edges[0], x_edges[-1], x_edges
    )

    y_taxis = uproot.writing.identify.to_TAxis(
        y_title, y_title, len(y_edges[:-1]), y_edges[0], y_edges[-1], y_edges
    )

    def add_2d_padding(A):
        nx, ny = A.shape
        return np.concatenate((np.zeros(ny), A.flatten(), np.zeros(ny))).reshape(
            nx + 2, ny
        )

    if add_empty_flow:
        H = add_2d_padding(add_2d_padding(H).T).T

    th2 = uproot.writing.identify.to_TH2x(
        hist_title,
        hist_title,
        np.ravel(H, order="C"),
        1,  # fEntries
        1,  # fTsumw
        1,  # fTsumw2
        1,  # fTsumwx
        1,  # fTsumwx2
        1,  # fTsumwy
        1,  # fTsumwy2
        1,  # fTsumwxy
        # np.array([1.0]),  # fSumw2
        np.ravel(np.ones_like(H), order="C"),  # fSumw2
        x_taxis,
        y_taxis,
    )
    return th2


def hist_to_th1(H, hist_name=""):
    __from_numpy = isinstance(H, tuple) and isinstance(H[0], np.ndarray)
    __from_dict = isinstance(H, dict)
    x_axis_edges = None
    x_axis_name = ""
    if __from_numpy:
        x_axis_edges = H[1]
    elif __from_dict:
        x_axis_edges = H["edges"]
    else:
        x_axis_edges = H.axes[0].edges
        x_axis_name = H.axes[0].name

    # take values and variances from hist and 'fill' under- and overflow bins
    values, variances = None, None
    if __from_numpy:
        values = H[0]
        variances = np.zeros_like(H[0])
    elif __from_dict:
        values = H["values"]
        variances = H.get("variances", np.zeros_like(values))
        if values.shape != variances.shape:
            print(variances.shape, values.shape)
            if variances.shape[1] == values.shape[0]:
                print("asdasd")
                variances = variances[0, :]
    else:
        values = H.values()
        variances = H.variances()
    values = np.concatenate(([0.0], values, [0.0]))
    variances = np.concatenate(([0.0], variances, [0.0]))

    x_taxis = uproot.writing.identify.to_TAxis(
        x_axis_name,
        x_axis_name,
        len(x_axis_edges) - 1,
        x_axis_edges[0],
        x_axis_edges[-1],
        x_axis_edges,
    )

    if hist_name == "":
        hist_name = x_axis_name

    th1 = uproot.writing.identify.to_TH1x(
        hist_name,
        hist_name,
        values,
        values.sum(),
        values.sum(),
        variances.sum(),
        1.0,
        1.0,
        variances,
        x_taxis,
    )

    return th1


def np_2d_hist_bin_value(vals, x, y):
    # x_bin = np.digitize([x],vals[1])[0]
    # if(x_bin > vals[1].shape[0]-1):
    #     x_bin = vals[1].shape[0]-1
    # elif(x_bin <= 0):
    #     x_bin = 1

    # y_bin = np.digitize([y],vals[2])[0]
    # if(y_bin > vals[2].shape[0]-1):
    #     y_bin = vals[2].shape[0]-1

    # elif(y_bin <=0):
    #     y_bin = 1
    # return vals[0][x_bin-1,y_bin-1]
    if isinstance(x, float):
        x = [x]
    x_bin = get_bin_indx(x, vals[1])
    if isinstance(y, float):
        y = [y]
    y_bin = get_bin_indx(y, vals[2])
    print(x_bin, y_bin)
    result = vals[0][x_bin, y_bin]
    if isinstance(x, ak.Array) and isinstance(y, ak.Array):
        result = ak.Array(result)
    return result


def get_bin_indx(values, edges):
    indx = np.digitize(ak.Array(values), edges) - 1
    indx = ak.where(indx == len(edges) - 1, len(edges) - 2, indx)
    indx = ak.where(indx < 0, 0, indx)
    return indx


def root_th2_bin_value(th2, x, y):
    x_bin = th2.GetXaxis().FindFixBin(x)
    if x_bin > th2.GetXaxis().GetNbins():
        x_bin = th2.GetXaxis().GetNbins()
    elif x_bin <= 0:
        x_bin = 1

    y_bin = th2.GetYaxis().FindFixBin(y)
    if y_bin > th2.GetYaxis().GetNbins():
        y_bin = th2.GetYaxis().GetNbins()
    elif y_bin <= 0:
        y_bin = 1

    return th2.GetBinContent(x_bin, y_bin)


def get_2d_hist_bin_content(H, x, y):
    if "TH2" in str(type(H)):
        return root_th2_bin_value(H, x, y)
    elif isinstance(H, tuple):
        return np_2d_hist_bin_value(H, x, y)


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
