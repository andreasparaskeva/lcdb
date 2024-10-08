#!/bin/bash
#PBS -l select=2:system=polaris
#PBS -l place=scatter
#PBS -l walltime=00:60:00
#PBS -q debug-scaling
#PBS -A datascience
#PBS -l filesystems=grand:home

set -xe

cd ${PBS_O_WORKDIR}

source /lus/grand/projects/datascience/regele/polaris/lcdb/publications/2023-neurips/build/activate-dhenv.sh

#!!! CONFIGURATION - START
source ./config.sh

export timeout=3500

export NDEPTH=8
export NRANKS_PER_NODE=8
export NNODES=`wc -l < $PBS_NODEFILE`
export NTOTRANKS=$(( $NNODES * $NRANKS_PER_NODE + 1))
export OMP_NUM_THREADS=$NDEPTH
export RANKS_HOSTS=$(python ../get_hosts_polaris.py)
#!!! CONFIGURATION - END

mkdir -p $LCDB_OUTPUT_RUN
pushd $LCDB_OUTPUT_RUN

# Enable MPS on each node allocated to job
export CUDA_MPS_PIPE_DIRECTORY=/tmp/nvidia-mps
export CUDA_MPS_LOG_DIRECTORY=/tmp/nvidia-log
${PBS_O_WORKDIR}/../enable_mps_polaris.sh

sleep 10

# Run experiment
mpiexec -n ${NTOTRANKS} -host ${RANKS_HOSTS} \
    --envall \
    ${PBS_O_WORKDIR}/../set_affinity_gpu_polaris.sh lcdb run \
    --openml-id $LCDB_OPENML_ID \
    --workflow-class $LCDB_WORKFLOW \
    --monotonic \
    --max-evals $LCDB_NUM_CONFIGS \
    --timeout $timeout \
    --initial-configs configs.csv \
    --timeout-on-fit 300 \
    --workflow-seed $LCDB_WORKFLOW_SEED \
    --valid-seed $LCDB_VALID_SEED \
    --test-seed $LCDB_TEST_SEED \
    --evaluator mpicomm


# Disable MPS on each node allocated to job
mpiexec -n ${NNODES} --ppn 1 ${PBS_O_WORKDIR}/../disable_mps_polaris.sh
