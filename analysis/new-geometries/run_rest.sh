#!/bin/bash
export PATH=/opt/mamba/envs/nuc/bin:$PATH
cd "$(dirname "$0")"
python neutronics.py "$@"
