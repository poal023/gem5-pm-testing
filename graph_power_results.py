import re
from itertools import cycle

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from matplotlib import (
    cm,
    colormaps,
)


def graph_singular(df):
    cmap = cm.get_cmap("Paired")  # or any colormap
    color_cycle = cycle(cmap.colors)  # Create infinite color iterator

    hatches = "".join(h * len(df) for h in " xx///\\")
    color = cm.inferno_r(np.linspace(0.4, 0.8, 30))
    ax = df.plot.bar(
        stacked=True,
        rot=0,
        edgecolor="black",
        color=[next(color_cycle) for _ in range(len(df.columns) + 4)],
    )
    bars = ax.patches

    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)
    ax.legend()

    plt.show()


def graph_all(df):
    colors = plt.cm.Paired.colors
    # df0 = df.pivot_table(index=["Benchmark"], columns=["CPU Type", "Simulator"], values=["Core", "L1D$", "L1I$", "L2$"])
    rows = df.shape[1]
    # cpus = ['Minor', 'O3', 'Timing']
    benchmarks = df["Benchmark"].unique()
    sims = df["Simulator"].unique()
    df = df.pivot_table(
        index=["Benchmark", "Simulator", "CPU Type"],
        values=["Core", "L1D$", "L1I$", "L2$"],
    ).sort_values(by=["Core", "L1D$", "L1I$", "L2$"])
    # df.set_index(["Benchmark", "Simulator", "CPU Type"])
    # df0 = df0.pivot_table(index=["CPU Type"], columns=["Simulator"])
    # df.set_index(["CPU Type", "Benchmark"], inplace=True)
    # df0 = df.reorder_levels(["Benchmark", "CPU Type"]).sort_index()
    # df0 = df0.unstack(level=-1)

    ax = df.plot(
        kind="bar",
        stacked=True,
        edgecolor="black",
        rot=-70,
        fontsize=18,
        width=0.85,
        figsize=(50, 20),
    )
    s = ax.get_xticks().tolist()
    print(df.iloc[0])
    ax.set_xlabel("(Benchmark, Simulator, CPU Type)", fontsize=21)
    ax.set_ylabel("Power (W)", fontsize=21)

    for tick in ax.xaxis.get_majorticklabels():
        tick.set_horizontalalignment("left")

    plt.subplots_adjust(bottom=0.3)
    plt.legend(fontsize=20)
    plt.title("Runtime Dynamic Power of Benchmarks", fontsize=24)
    # plt.tight_layout()
    plt.show()


def bmrk_name(name):
    if "iaxpy" in name:
        return "IAXPY"
    elif "saxpy" in name:
        return "SAXPY"
    elif "daxpy" in name:
        return "DAXPY"
    elif "iax" in name:
        return "IAX"
    elif "sax" in name:
        return "SAX"
    elif "hello-world" in name:
        return "Hello World"
    else:
        return name[name.rindex("_") + 1 :]


def cpu_name(name):
    if "o3" in name:
        return "O3"
    elif "minor" in name:
        return "Minor"
    elif "timing" in name:
        return "Timing"
    else:
        return "Unknown"


def main():
    root_dir = "./mcpat-runs/power_results"
    benchmarks = ["hello-world", "iax", "iaxpy", "sax", "saxpy", "daxpy"]
    cpus = ["timing", "minor", "o3"]

    # print(df.head())

    dfs = []
    row_names = []
    for b in benchmarks:
        for c in cpus:
            df = pd.read_csv(f"{root_dir}/{b}_{c}_power_results.csv")
            df = df.set_index(df.columns[0]).rename_axis("Name")
            dfs.append(df)
            row_names.append(df.index.tolist())

    row_names = list(np.array(row_names).flat)
    all_dfs = pd.concat(dfs, axis=0, ignore_index=True)
    all_dfs["Name"] = row_names
    # all_dfs.set_index('Name')

    # print(all_dfs.drop(df.index[0]))
    # print(all_dfs[all_dfs['Name'].str.contains('^(?=.*(iax))(?!.*iaxpy).*$', case=False)])
    all_dfs["Simulator"] = all_dfs["Name"].apply(
        lambda x: "McPAT" if "mcpat" in x else "gem5"
    )
    all_dfs["Benchmark"] = all_dfs["Name"].apply(bmrk_name)
    all_dfs["CPU Type"] = all_dfs["Name"].apply(cpu_name)
    print(all_dfs[all_dfs["Benchmark"] == "DAXPY"])

    # graph_singular(all_dfs[all_dfs['CPU Type'] == "O3"])
    graph_all(all_dfs)


if __name__ == "__main__":
    main()
