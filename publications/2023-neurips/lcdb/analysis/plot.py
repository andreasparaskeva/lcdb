import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from deephyper.analysis import rank
from matplotlib.colors import LinearSegmentedColormap

from .json import (
    QueryAnchorValues,
    QueryEpochValues,
    QueryMetricValuesFromAnchors,
    QueryMetricValuesFromEpochs
)
from .score import balanced_accuracy_from_confusion_matrix


def plot_learning_curves(
    fidelity_values,
    metric_values,
    mode="min",
    rank_method="ordinal",
    decimals=5,
    alpha=1.0,
    metric_value_baseline=None,
    plot_worse_than_baseline=True,
    ax=None,
    cmap=None,
    **kwargs,
):

    if len(fidelity_values) != len(metric_values[0]):
        raise ValueError(
            f"metric_values has {len(metric_values[0])} fidelities, "
            f"but {len(fidelity_values)} values are given in fidelity_values."
        )

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure()

    # corresponds to iloc indexing
    if metric_value_baseline is not None:
        metric_max_fidelity = np.asarray(
            [metric_value_baseline] + [y[-1] for y in metric_values]
        )
    else:
        metric_max_fidelity = np.asarray([y[-1] for y in metric_values])

    if mode == "max":
        ranking = rank(-metric_max_fidelity, decimals=decimals, method=rank_method)
    elif mode == "min":
        ranking = rank(metric_max_fidelity, decimals=decimals, method=rank_method)
    else:
        raise ValueError(f"Unknown mode '{mode}' should be 'max' or 'min'.")

    if metric_value_baseline is not None and cmap is None:
        ranking_baseline = ranking[0]
        ranking = ranking[1:]

        center = ranking_baseline / max(ranking)
        q1 = center / 2
        q3 = center + (1 - center) / 2

        cmap = LinearSegmentedColormap.from_list(
            "custom",
            (
                # Edit this gradient at https://eltos.github.io/gradient/#0:00D0FF-25:0000FF-75:FF0000-100:FFD800
                (0.000, (0.000, 0.816, 1.000)),
                (q1, (0.000, 0.000, 1.000)),
                (q3, (1.000, 0.000, 0.000)),
                (1.000, (1.000, 0.847, 0.000)),
            ),
        )

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

    ranking_max = ranking.max()
    for i, y in enumerate(metric_values):
        if not plot_worse_than_baseline:
            # if mode == "min" and metric_value_baseline and all(map(lambda yi: yi > metric_value_baseline , y)):
            if mode == "min" and metric_value_baseline is not None and y[-1] > metric_value_baseline:
                continue
            elif mode == "max" and metric_value_baseline is not None and -y[-1] > metric_value_baseline:
                continue
        ax.plot(fidelity_values, y, color=cmap(ranking[i] / ranking_max), alpha=alpha)

    ax.grid()

    norm = mpl.cm.ScalarMappable(norm=None, cmap=cmap)
    norm.set_clim(1, ranking_max)
    cb = plt.colorbar(norm, ax=plt.gca(), label="Rank")
    if metric_value_baseline is not None:
        cb.ax.axhline(ranking_baseline, c="lime", linewidth=2, linestyle="--")
    return fig, ax


def get_observation_curve_data_numpy(df_results):

    res = get_observation_curve_data_nonaveraged(df_results)

    df_processed = pd.DataFrame(res)

    config_ids = df_processed['config_id'].unique()
    val_seeds = df_processed['val_seed'].unique()
    test_seeds = df_processed['test_seed'].unique()
    anchor_ids = df_processed['anchor_id'].unique()
    splits = df_processed['split'].unique()

    assert(len(splits) == 3)

    results_array = np.full((len(config_ids), len(val_seeds), len(test_seeds), len(anchor_ids), 3), fill_value=np.nan)

    for row_id in range(len(df_processed)):

        row = df_processed.iloc[row_id]
        
        config_id = row['config_id']
        val_seed = row['val_seed']
        test_seed = row['test_seed']
        anchor_id = row['anchor_id']

        split = row['split']
        if split == 'train':
            split_id = 0
        if split == 'val':
            split_id = 1
        if split == 'test':
            split_id = 2

        results_array[config_id, val_seed, test_seed, anchor_id, split_id] = row['error_rate']

    return results_array


def get_observation_curve_data(df_results, split='val'):
    l = []
    hp_columns = [c for c in df_results.columns if c.startswith("p:")]

    for hp_config, df_hp_config in df_results.groupby(hp_columns):
        source = df_hp_config["m:json"]
        query_anchor_values = QueryAnchorValues()
        anchor_values = source.apply(query_anchor_values).to_list()

        query_confusion_matrix_values = QueryMetricValuesFromAnchors("confusion_matrix", split_name=split)
        out = source.apply(query_confusion_matrix_values)

        balanced_error_rate_values = np.array(out.apply(lambda x: list(map(lambda x: 1 - balanced_accuracy_from_confusion_matrix(x), x))).to_list())
        l.append(np.mean(balanced_error_rate_values, axis=0))

    balanced_error_rate_values = np.array(l)

    for i, (xi, yi) in enumerate(zip(anchor_values, l)):
        anchor_values[i] = xi[:len(yi)]

    return (anchor_values, balanced_error_rate_values)

def get_observation_curve_data_nonaveraged(df_results):
    hp_columns = [c for c in df_results.columns if c.startswith("p:")]

    anchor_values_total = []

    for i in range(len(df_results)):

        row = df_results.iloc[i]
        source = row["m:json"]
        query_anchor_values = QueryAnchorValues()
        anchor_values = query_anchor_values(source)
        for anchor in anchor_values:
            anchor_values_total.append(anchor)

    anchor_values_total = set(anchor_values_total)
    anchor_values_total = list(anchor_values_total)
    anchor_values_total.sort()
    print(anchor_values_total)

    res = []

    config_id = 0
    for hp_config, df_hp_config in df_results.groupby(hp_columns):
        for i in range(len(df_hp_config)):

            row = df_hp_config.iloc[i]
            source = row["m:json"]
            query_anchor_values = QueryAnchorValues()
            anchor_values = query_anchor_values(source)

            for split in ['train', 'val', 'test']:

                query_confusion_matrix_values = QueryMetricValuesFromAnchors("confusion_matrix", split_name=split)
                out = query_confusion_matrix_values(source)

                val_seed = row['m:valid_seed']
                test_seed = row['m:test_seed']

                get_error_rate = lambda x: 1 - balanced_accuracy_from_confusion_matrix(x)
                error_rates = []
                for cm in out:
                    error_rates.append(get_error_rate(cm))

                assert(len(error_rates) == len(anchor_values))

                for anchor_id in range(len(error_rates)):
                    actual_anchor = anchor_values[anchor_id]
                    anchor_index = anchor_values_total.index(actual_anchor)
                    res.append({"config_id": config_id, "val_seed": val_seed, "test_seed": test_seed, "anchor_id": anchor_index, "split": split, "error_rate": error_rates[anchor_id]})

        config_id = config_id + 1

    return res


def plot_observation_curves(df_results, ax=None):
    l = []
    hp_columns = [c for c in df_results.columns if c.startswith("p:")]

    for hp_config, df_hp_config in df_results.groupby(hp_columns):
        source = df_hp_config["m:json"]
        query_anchor_values = QueryAnchorValues()
        anchor_values = source.apply(query_anchor_values).to_list()

        query_confusion_matrix_values = QueryMetricValuesFromAnchors("confusion_matrix", split_name="val")
        out = source.apply(query_confusion_matrix_values)

        balanced_error_rate_values = np.array(out.apply(lambda x: list(map(lambda x: 1 - balanced_accuracy_from_confusion_matrix(x), x))).to_list())
        l.append(np.mean(balanced_error_rate_values, axis=0))

    balanced_error_rate_values = np.array(l)

    for i, (xi, yi) in enumerate(zip(anchor_values, l)):
        anchor_values[i] = xi[:len(yi)]

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure()
    plot_learning_curves(anchor_values, balanced_error_rate_values, metric_value_baseline=balanced_error_rate_values[0][-1], ax=ax)
    ax.axhline(y=balanced_error_rate_values[0][-1], color="lime", linestyle="--")
    ax.set_xlabel(f"Number of Samples")
    ax.set_ylabel(f"Validation Balanced Error Rate")
    ax.set_xscale("log")
    ax.set_yscale("log")
    return fig, ax


def plot_observation_curves(df_results):
    mean_balanced_error_rates_of_configs = []
    hp_columns = [c for c in df_results.columns if c.startswith("p:")]

    if len(pd.unique(df_results["m:openmlid"])) > 1:
        raise ValueError(
            "Given dataframe has results for more than one dataset, which is not allowed for observation curves."
        )

    anchor_values = None
    for hp_config, df_hp_config in df_results.groupby(hp_columns):
        source = df_hp_config["m:json"]

        # get anchors (and check that they are consistent)
        query_anchor_values = QueryAnchorValues()
        _anchor_values = source.apply(query_anchor_values).to_list()[0]
        if anchor_values is None:
            anchor_values = _anchor_values
        else:
            if len(anchor_values) != len(_anchor_values):
                raise ValueError(f"Inconsistent number of anchors across configurations.")

        # get confusion matrix for config and compute balanced error rate
        query_confusion_matrix_values = QueryMetricValuesFromAnchors("confusion_matrix", split_name="val")
        out = source.apply(query_confusion_matrix_values)
        balanced_error_rate_values_for_config = np.array(out.apply(lambda x: list(map(lambda x: 1 - balanced_accuracy_from_confusion_matrix(x), x))).to_list())
        mean_balanced_error_rates_of_configs.append(balanced_error_rate_values_for_config.mean(axis=0))

    fig, ax = plt.subplots()
    plot_learning_curves(
        anchor_values,
        mean_balanced_error_rates_of_configs,
        metric_value_baseline=mean_balanced_error_rates_of_configs[0][-1],
        ax=ax
    )
    ax.axhline(y=mean_balanced_error_rates_of_configs[0][-1], color="lime", linestyle="--")
    ax.set_xlabel(f"Number of Samples")
    ax.set_ylabel(f"Validation Balanced Error Rate")
    ax.set_xscale("log")
    ax.set_yscale("log")
    return fig, ax


def plot_iteration_curves_dataset(df_results, metric="balanced_accuracy", sample_anchor=-1, log_x=False, log_y=True):

    # throw-out
    df_results = df_results[df_results["m:json"].notna()]

    l = []
    hp_columns = [c for c in df_results.columns if c.startswith("p:")]

    epoch_values_per_config = []
    for hp_config, df_hp_config in df_results.groupby(hp_columns):
        source = df_hp_config["m:json"]
        query_epoch_values = QueryEpochValues()
        epoch_values = np.array(source.apply(query_epoch_values).to_list())
        epoch_values_per_config.append(epoch_values[0][sample_anchor])  # should be the same for all repetitions of this config

        if metric in ["brier_score", "log_loss"]:
            query_metric = metric
            metric_map = lambda x: x
        else:
            query_metric = "confusion_matrix"
            metric_map = lambda val: 1 - balanced_accuracy_from_confusion_matrix(val),
        base_values = source.apply(QueryMetricValuesFromEpochs(query_metric, split_name="val"))

        # extract epoch-wise balanced error rate (this cannot generally be translated to an array due to different epoch counts)
        balanced_error_rate_values = base_values.apply(
            lambda sample_wise_values: list(map(
                metric_map,
                sample_wise_values[sample_anchor]  # this is the list of epoch-wise values for this sample anchor
            ))
        ).to_list()  # only get values from desired sample anchor
        l.append(np.mean(balanced_error_rate_values, axis=0))

    balanced_error_rate_values = np.array(l)

    fig, ax = plt.subplots()
    plot_learning_curves(epoch_values_per_config, balanced_error_rate_values, metric_value_baseline=balanced_error_rate_values[0][-1], ax=ax)
    ax.axhline(y=balanced_error_rate_values[0][-1], color="lime", linestyle="--")
    ax.set_xlabel(f"Number of Iterations")
    ax.set_ylabel(f"Validation Balanced Error Rate")
    if log_x:
        ax.set_xscale("log")
    if log_y:
        ax.set_yscale("log")
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
