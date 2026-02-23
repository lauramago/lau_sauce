#!/bin/bash
#BSUB -J rf3[1-2]
#BSUB -q gpua100
#BSUB -n 4
#BSUB -W 4:00
#BSUB -R "rusage[mem=10GB]"
#BSUB -R "span[hosts=1]"
#BSUB -gpu "num=1:mode=exclusive_process"
#BSUB -o logs/rf3_%I.stdout
#BSUB -B
#BSUB -N

module load cuda/12.4

export MY_PATH="/dtu/projects/dbl/rf3/release" 
export PYTHON_PATH="${{MY_PATH}}:{{PYTHON_PATH:-}}" 
source /dtu/projects/dbl/foundry/miniforge3/etc/profile.d/conda.sh 
conda activate /dtu/projects/dbl/rf3/release/conda_envs/rf3-env

PER_TASK=10
START_NUM=$(( ($LSB_JOBINDEX -1) * $PER_TASK +1))
END_NUM=$(( $LSB_JOBINDEX * $PER_TASK ))


for ((run=$START_NUM; run<=$END_NUM; run++ )); do
  echo This is LSF task $LSB_JOBINDEX, run number $run
  CMD=$(sed -n "${run}p" /work3/kiersum/projects/enzyme_design/hydrolases/serine_hydrolase/rd1/cmds/rf3.cmds
)
  echo "${CMD}" | bash




done
