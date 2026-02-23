# DBL_secrets

<img alt="secret_sauce" src="assets/secret_sauce.png" />

Jupyter notebooks for running protein design campaigns in the DBL. Two pipelines are available:

| Pipeline | Notebook | Use case |
|---|---|---|
| Enzyme design | `enzdes_pipeline-main/enzyme_design.ipynb` | De novo enzyme design around a theozyme |
| Binder design | `GPCR_binder_pipeline/binder_design.ipynb` | De novo protein binder design against a target |

Both follow the same three-step workflow:

```
RFD3  →  MPNN  →  RF3
```

---

## Prerequisites

- Access to the DTU HPC cluster (LSF job scheduler)
- Model checkpoints and environments are pre-installed under `/dtu/projects/dbl/` — no manual installation needed
- Miniforge3 installed in your scratch space (see setup below)

---

## Setup

### 1. Clone the repository

```bash
cd /work3/$USER/
git clone <repo-url> DBL_secrets
```

The notebooks run directly from the cloned repo — no need to move them.

### 2. Install Miniforge3 (if not already done)

```bash
cd /work3/$USER/
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
```

### 3. Create and register the environment

**Enzyme design:**
```bash
conda env create -f enzdes_pipeline-main/enzdes.yml
conda activate enzdes
python -m ipykernel install --user --name cgrp_env1 --display-name "enzdes"
```

**Binder design:**
```bash
conda env create -f GPCR_binder_pipeline/binder.yml
conda activate cgrp_env1
python -m ipykernel install --user --name cgrp_env1 --display-name "binder_design"
```

### 4. Open the notebook in Jupyter and select the correct kernel

- Enzyme design → kernel: `enzdes`
- Binder design → kernel: `binder_design`

---

## Output directory structure

Design outputs are written **outside the repo** into your scratch space, keeping the repo clean. The structure is created automatically when you run the setup cell.

**Enzyme design** (`/work3/$USER/projects/enzyme_design/`):
```
{family}/
└── {target}/
    └── {campaign}/
        ├── inputs/          ← place your input PDB here
        ├── configs/         ← RFD3 and RF3 JSON configs
        ├── diffusion_out/   ← RFD3 output structures
        ├── mpnn_out/        ← MPNN output FASTAs
        ├── rf3_out/         ← RF3 predicted structures
        ├── scores/          ← metrics CSVs
        ├── cmds/            ← job command files and submit scripts
        └── logs/            ← HPC job logs
```

**Binder design** (`/work3/$USER/projects/binder_design/`):
```
{campaign}/
└── {experiment}/
    ├── inputs/          ← place your input PDB here
    ├── configs/         ← RFD3 and RF3 JSON configs (incl. rf3_template.json)
    ├── diffusion_out/   ← RFD3 output structures
    ├── mpnn_out/        ← MPNN output FASTAs
    ├── rf3_out/         ← RF3 predicted structures
    ├── scores/          ← metrics CSVs
    ├── cmds/            ← job command files
    ├── submit/          ← LSF submit scripts
    └── logs/            ← HPC job logs
```

---

## A note on example cell outputs

The notebooks contain pre-run cell outputs to illustrate what each step produces. These come from real campaigns and show the expected tables, metrics, and plots. The paths shown in those outputs (`/work3/kiersum/...`, `/work3/marhr/...`) will differ from yours — that is expected. Your outputs will appear under `/work3/$USER/...` with the structure above.
