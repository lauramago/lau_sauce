import os
import json
import sys
import numpy as np
import math


# writes submission script for job in LSF cluster
def make_sub_script(cmds,n_task,cores=1,mem='6G',time_limit='12:00',queue='cabl40s',gpu=False,group_size=1,job_name='slurm',env=None,python_path=None):
    gpu_queue = f'#BSUB -gpu "{gpu}"' if gpu else ''
    python_path = f'export MY_PATH="{python_path}" \nexport PYTHON_PATH=\"${{{{MY_PATH}}}}:{{{{PYTHON_PATH:-}}}}" ' if python_path else ''
    env = f'source /dtu/projects/dbl/foundry/miniforge3/etc/profile.d/conda.sh \nconda activate {env}' if env else ''
    
    shell_txt = \
f"""#!/bin/bash
#BSUB -J {job_name}[1-{math.ceil(n_task/group_size)}]
#BSUB -q {queue}
#BSUB -n {cores}
#BSUB -W {time_limit}
#BSUB -R "rusage[mem={mem}]"
#BSUB -R "span[hosts=1]"
{gpu_queue}
#BSUB -o logs/{job_name}_%I.stdout
#BSUB -B
#BSUB -N

module load cuda/12.4

{python_path}
{env}

PER_TASK={group_size}
START_NUM=$(( ($LSB_JOBINDEX -1) * $PER_TASK +1))
END_NUM=$(( $LSB_JOBINDEX * $PER_TASK ))


for ((run=$START_NUM; run<=$END_NUM; run++ )); do
  echo This is LSF task $LSB_JOBINDEX, run number $run
  CMD=$(sed -n \"${{run}}p\" {cmds}
)
  echo \"${{CMD}}\" | bash




done
"""
    os.makedirs('logs',exist_ok=True)
    sub_script = cmds.replace('.cmds','.sh')
    
    with open(sub_script,'w') as f:
        f.write(shell_txt)
    
    return


# config json for backbone generation with RFD3
def write_rfd3_json(json_f, input_pdb, contig, length, dialect=2, ligand=None, fixed_atoms=None, catres=None, hotspots=None, select_hb_acc=None,select_hb_donor=None,
                    redesign_motif_sc=False,infer_ori_strategy=None,is_non_loopy=True):
    
    design_name = os.path.basename(input_pdb)[:-4]
    
    payload = {
    design_name: {
        "dialect": dialect,
        "input": input_pdb,
        "contig": contig,
        "length": length,
        "redesign_motif_sidechains": redesign_motif_sc,
        "is_non_loopy": is_non_loopy
    }
}

    optional_fields = {
        "ligand": ligand,
        "select_fixed_atoms": fixed_atoms,
        "infer_ori_strategy": infer_ori_strategy,
        "select_hotspots": hotspots,
        "select_hbond_donor": select_hb_donor,
        "select_hbond_acceptor": select_hb_donor,
}

    payload[design_name].update({k: v for k, v in optional_fields.items() if v is not None})

    with open(json_f,"w") as f:
        json.dump(payload, f, indent=4) 

    return
