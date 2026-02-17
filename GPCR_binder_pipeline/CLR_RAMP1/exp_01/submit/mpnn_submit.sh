#!/bin/sh
### General options
#BSUB -q hpc
#BSUB -J mpnn[1-1]
#BSUB -n 4
#BSUB -W 2:00
#BSUB -R "rusage[mem=10GB]"
#BSUB -o /work3/marhr/Projects/dbl/binder_design_pipeline/CLR_RAMP1/exp_01/logs//mpnn_%J_%I.out
#BSUB -e /work3/marhr/Projects/dbl/binder_design_pipeline/CLR_RAMP1/exp_01/logs//mpnn_%J_%I.err
# -- end of LSF options --

# Ensure logs directory exists
mkdir -p "/work3/marhr/Projects/dbl/binder_design_pipeline/CLR_RAMP1/exp_01/logs/"

# Activate environment
source /dtu/projects/dbl/LigandMPNN/25.3.1-0//miniforge3/bin/activate ligandmpnn_env
export MPNN_PATH="/dtu/projects/dbl/LigandMPNN/25.3.1-0/"
export PYTHONPATH="${MPNN_PATH}:${PYTHONPATH:-}"

# Load file mapping for this array job
MAPPING_FILE="/work3/marhr/Projects/dbl/binder_design_pipeline/CLR_RAMP1/exp_01/submit/mpnn_file_mapping.json"
ARRAY_INDEX=$LSB_JOBINDEX

# Extract files for this array index from JSON
FILES=$(python3 -c "import json, sys; data=json.load(open(sys.argv[1])); print(' '.join(data['file_mapping'][str(sys.argv[2])]))" "$MAPPING_FILE" "$ARRAY_INDEX")

# Process each file assigned to this array job
for STRUCTURE_FILE in $FILES; do
    echo "Processing: $STRUCTURE_FILE"

    # Create output directory for this file
    BASENAME=$(basename "$STRUCTURE_FILE" .cif.gz)
    BASENAME=$(basename "$BASENAME" .pdb)
    OUT_DIR="/work3/marhr/Projects/dbl/binder_design_pipeline/CLR_RAMP1/exp_01/mpnn_out//${BASENAME}"
    mkdir -p "$OUT_DIR"

    # Run MPNN
    python "${MPNN_PATH}/run.py" \
        --seed 42 \
        --pdb_path "$STRUCTURE_FILE" \
        --out_folder "$OUT_DIR" \
        --batch_size 5 \
        --number_of_batches 1 \
        --model_type "protein_mpnn" \
        --checkpoint_protein_mpnn "/dtu/projects/dbl/LigandMPNN/25.3.1-0//model_params/proteinmpnn_v_48_020.pt" \
        --chains_to_design "A"

    echo "Completed: $STRUCTURE_FILE"
done

echo "Array job $LSB_JOBINDEX completed at $(date)"
