#!/bin/sh
#BSUB -q gpuv100
#BSUB -J rfd3
#BSUB -n 4
#BSUB -gpu "num=1:mode=exclusive_process"
#BSUB -W 12:00
#BSUB -R "rusage[mem=10GB]"
#BSUB -R "span[hosts=1]"
#BSUB -o /work3/laugon/desktop/TCR_designs/tcr_cdr3/exp_01/logs/%J.out
#BSUB -e /work3/laugon/desktop/TCR_designs/tcr_cdr3/exp_01/logs/%J.err

mkdir -p /work3/laugon/desktop/TCR_designs/tcr_cdr3/exp_01/logs
module load cuda/12.4
source /dtu/projects/dbl/foundry/miniforge3/etc/profile.d/conda.sh
conda activate /dtu/projects/dbl/foundry/miniforge3/envs/rfd3

export RFD3_PATH="/dtu/projects/dbl/foundry"
export PYTHONPATH="${RFD3_PATH}:${PYTHONPATH:-}"

mkdir -p "/work3/laugon/desktop/TCR_designs/tcr_cdr3/exp_01/diffusion_out"
echo "Output directory: /work3/laugon/desktop/TCR_designs/tcr_cdr3/exp_01/diffusion_out"

rfd3 design \
    out_dir="/work3/laugon/desktop/TCR_designs/tcr_cdr3/exp_01/diffusion_out" \
    inputs="/work3/laugon/desktop/TCR_designs/tcr_cdr3/exp_01/configs/TCR_CDR3ab_rfd3.json" \
    ckpt_path="/dtu/projects/dbl/foundry/ckpt/rfd3_latest.ckpt" \
    diffusion_batch_size=2 \
    n_batches=2 \
    inference_sampler.step_scale=3 \
    inference_sampler.gamma_0=0.2

echo "Completed at $(date)"
