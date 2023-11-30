#!/bin/bash

export LCDB_NUM_CONFIGS=1000
export LCDB_WORKFLOW=lcdb.workflow.sklearn.LibLinearWorkflow
export LCDB_OPENML_ID=38
export LCDB_WORKFLOW_SEED=42
export LCDB_VALID_SEED=42
export LCDB_TEST_SEED=42

export LCDB_OUTPUT_WORKFLOW=$PWD/output/$LCDB_WORKFLOW
export LCDB_INITIAL_CONFIGS=$LCDB_OUTPUT_WORKFLOW/initial_configs.csv
export LCDB_OUTPUT_DATASET=$LCDB_OUTPUT_WORKFLOW/$LCDB_OPENML_ID
export LCDB_OUTPUT_RUN=$LCDB_OUTPUT_DATASET/$LCDB_VALID_SEED-$LCDB_TEST_SEED-$LCDB_WORKFLOW_SEED
