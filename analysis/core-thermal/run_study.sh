#!/bin/bash
# Full core-thermal study run (OpenMC-heavy). Logs to results/study.log.
set -x
export PATH=/opt/mamba/envs/nuc/bin:$PATH OMP_THREADS=4
cd "$(dirname "$0")"
python pool.py calibrate
python pool_study.py
python validate.py godiva p1 infinite finite
python simulate.py all
