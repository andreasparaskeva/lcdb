import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from deephyper.analysis import rank
from matplotlib.colors import LinearSegmentedColormap


def plot_learning_curves(
    fidelity_values,
    metric_values,
    mode="min",
    rank_method="ordinal",
    decimals=5,
    alpha=1.0,
    ax=None,
    cmap=None,
    **kwargs,
):
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure()

    if cmap is None:
        cmap = LinearSegmentedColormap.from_list(
            "custom",
            (
                # Edit this gradient at https://eltos.github.io/gradient/#0:00D0FF-25:0000FF-75:FF0000-100:FFD800
                (0.000, (0.000, 0.816, 1.000)),
                (0.250, (0.000, 0.000, 1.000)),
                (0.750, (1.000, 0.000, 0.000)),
                (1.000, (1.000, 0.847, 0.000)),
            ),
        )
    elif isinstance(cmap, str):
        cmap = mpl.colormaps[cmap]
    else:
        cmap = cmap

    # corresponds to iloc indexing
    metric_max_fidelity = np.asarray([y[-1] for y in metric_values])

    if mode == "max":
        ranking = rank(-metric_max_fidelity, decimals=decimals, method=rank_method)
    elif mode == "min":
        ranking = rank(metric_max_fidelity, decimals=decimals, method=rank_method)
    else:
        raise ValueError(f"Unknown mode '{mode}' should be 'max' or 'min'.")

    ranking_max = ranking.max()
    for i, (x, y) in enumerate(zip(fidelity_values, metric_values)):
        ax.plot(x, y, color=cmap(ranking[i] / ranking_max), alpha=alpha)

    ax.grid()

    norm = mpl.cm.ScalarMappable(norm=None, cmap=cmap)
    norm.set_clim(1, ranking_max)
    plt.colorbar(norm, ax=plt.gca(), label="Rank")
    # plt.xlim(0, fidelities.max())

    return fig, ax


def pad_with_last(x, max_len):
    if len(x) < max_len:
        return x + [x[-1]] * (max_len - len(x))
    else:
        return x


def plot_regret_from_topk(fidelity_values, metric_values, topk=10, ax=None):
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure()

    max_len = max(map(len, metric_values))

    # The x values to plot
    for x in fidelity_values:
        if len(x) == max_len:
            break

    metric_values = list(map(lambda x: pad_with_last(x, max_len), metric_values))
    metric_values = np.asarray(metric_values)

    # The best score at the maximum fidelity
    y_star = metric_values[:, -1].min(axis=0)

    # Compute the regrets
    idx_selected = map(lambda x: np.argpartition(x, kth=topk)[:topk], metric_values.T)
    regrets = list(map(lambda idx: (metric_values[idx, -1] - y_star), idx_selected))
    regrets_median = np.median(regrets, axis=1)
    regrets_min = np.quantile(regrets, q=0.1, axis=1)
    regrets_max = np.quantile(regrets, q=0.9, axis=1)

    ax.plot(x, regrets_median)
    ax.fill_between(x, regrets_min, regrets_max, alpha=0.2)
    ax.grid()

    return fig, ax
