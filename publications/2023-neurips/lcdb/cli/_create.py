"""Command line to create/generate new experiments."""

import sys
import json

from ..workflow._util import get_all_experiments, get_experimenter


def add_subparser(subparsers):
    """
    :meta private:
    """
    subparser_name = "create"
    function_to_call = main

    subparser = subparsers.add_parser(
        subparser_name, help="Create new experiments from a configuration file."
    )

    subparser.add_argument(
        "--workflow", type=str, required=True, help="Name of workflow class."
    )
    subparser.add_argument(
        "--num_configs",
        type=int,
        required=False,
        default=10,
        help="The number of hyperparameter configurations that are being sampled.",
    )
    subparser.set_defaults(func=function_to_call)


def main(workflow: str, *args, **kwargs):
    """
    :meta private:
    """

    # get workflow class
    workflow_class = getattr(sys.modules["lcdb.workflow"], workflow)

    # create experiment rows
    experiments = get_all_experiments(workflow_class=workflow_class)

    # filter experiments
    if hasattr(workflow_class, "is_experiment_valid"):
        experiments = [e for e in experiments if workflow_class.is_experiment_valid(e)]

    # replace hyperparameters by strings
    for e in experiments:
        e["hyperparameters"] = json.dumps(e["hyperparameters"])
        e["train_sizes"] = json.dumps(e["train_sizes"])

    # create all rows for the experiments
    get_experimenter(workflow_class).fill_table_with_rows(rows=experiments)
