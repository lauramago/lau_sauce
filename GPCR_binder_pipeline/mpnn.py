#!/usr/bin/env -S /bin/sh -c '"/dtu/projects/dbl/proteusai/latest/proteus_shebang.sh" "$0" "$@"'
import sys
sys.path.insert(0, "/dtu/projects/dbl/proteusai/latest/pai/src")
 
from glob import glob
from pai.hpc.mpnn import create_and_write_mpnn_array_job
from pai.metrics.structure import compute_structure_metrics
from atomworks.io import parse
 
from tqdm import tqdm
 
# Get structure files
structure_files = sorted(glob("/work3/marhr/Projects/rfd3/PAC1R/exp_05/rf3_out_redesign1_1/filtered_best_for_redesign2/*.cif.gz"))
n_structures = len(structure_files)

# OPTIONALLY REMOVE BAD STRUCTURES
for f in tqdm(structure_files, desc="Computing metrics"):
    structure = parse(f)
    metrics = compute_structure_metrics(structure["asym_unit"][0] )
    if metrics["n_chainbreaks"] > 0 or metrics["n_clashes_sidechain"] > 0 or metrics["n_clashes_backbone"] > 0:
        structure_files.remove(f)
 
print(f"Removed {n_structures - len(structure_files)} structures with chainbreaks, sidechain clashes, or backbone clashes")
 
# Create MPNN array job (CPU-only)
result = create_and_write_mpnn_array_job(
    pdb_files=structure_files,
    n_chunks=20,
)

