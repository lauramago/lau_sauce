#!/bin/bash
#BSUB -J mpnn[1-2]
#BSUB -q hpc
#BSUB -n 4
#BSUB -W 2:00
#BSUB -R "rusage[mem=10G]"
#BSUB -R "span[hosts=1]"

#BSUB -o logs/mpnn_%I.stdout
#BSUB -B
#BSUB -N

module load cuda/12.4

export MY_PATH="/dtu/projects/dbl/LigandMPNN/25.3.1-0/" 
export PYTHON_PATH="${{MY_PATH}}:{{PYTHON_PATH:-}}" 
source /dtu/projects/dbl/foundry/miniforge3/etc/profile.d/conda.sh 
conda activate /dtu/projects/dbl/LigandMPNN/25.3.1-0//miniforge3/envs/ligandmpnn_env

PER_TASK=10
START_NUM=$(( ($LSB_JOBINDEX -1) * $PER_TASK +1))
END_NUM=$(( $LSB_JOBINDEX * $PER_TASK ))


for ((run=$START_NUM; run<=$END_NUM; run++ )); do
  echo This is LSF task $LSB_JOBINDEX, run number $run
  CMD=$(sed -n "${run}p" /work3/kiersum/projects/enzyme_design/hydrolases/serine_hydrolase/rd1/cmds/mpnn.cmds
)
  echo "${CMD}" | bash




done
