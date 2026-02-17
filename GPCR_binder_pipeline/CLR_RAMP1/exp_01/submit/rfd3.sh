#!/bin/sh
#BSUB -q cabl40s
#BSUB -J rfd3
#BSUB -n 4
#BSUB -gpu "num=1:mode=exclusive_process"
#BSUB -W 12:00
#BSUB -R "rusage[mem=10GB]"
#BSUB -R "span[hosts=1]"
##BSUB -u marhr@dtu.dk
#BSUB -B
#BSUB -N
#BSUB -o /work3/marhr/Projects/dbl/binder_design_pipeline/CLR_RAMP1/exp_01/logs//%J.out
#BSUB -e /work3/marhr/Projects/dbl/binder_design_pipeline/CLR_RAMP1/exp_01/logs//%J.err

# Ensure logs directory exists
mkdir -p /work3/marhr/Projects/dbl/binder_design_pipeline/CLR_RAMP1/exp_01/logs/

# Load modules
module load cuda/12.4

# Activate miniforge environment
source /dtu/projects/dbl/foundry/miniforge3/etc/profile.d/conda.sh
conda activate /dtu/projects/dbl/foundry/miniforge3/envs/rfd3

# Set environment variables
export RFD3_PATH="/dtu/projects/dbl/foundry"
export PYTHONPATH="${RFD3_PATH}:${PYTHONPATH:-}"

# Input and output
INPUT_JSON="/work3/marhr/Projects/dbl/CLR_RAMP1/exp_01/configs/CLR_RAMP1_rfd3_test.json"
OUT_DIR="/work3/marhr/Projects/dbl/binder_design_pipeline/CLR_RAMP1/exp_01/diffusion_out/"
mkdir -p "$OUT_DIR"

echo "Processing: $INPUT_JSON"
echo "Output directory: $OUT_DIR"

# Checkpoint
CKPT_PATH="/dtu/projects/dbl/foundry/ckpt/rfd3_latest.ckpt"

# Run rfd3 design
rfd3 design \
    out_dir="$OUT_DIR" \
    inputs="$INPUT_JSON" \
    ckpt_path="$CKPT_PATH" \
    diffusion_batch_size=2 \
    n_batches=2

echo "Completed: $INPUT_JSON at $(date)"
