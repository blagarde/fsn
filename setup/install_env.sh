#!/usr/bin/env bash
# Create the conda environment with NJOY2016 and OpenMC (both from conda-forge) and install this package.
# Usage: bash setup/install_env.sh [prefix]   (default prefix /opt/mamba)
set -euo pipefail
PREFIX="${1:-/opt/mamba}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$PREFIX/bin"
if [ ! -x "$PREFIX/bin/micromamba" ]; then
  curl -fsSL -m 300 https://conda.anaconda.org/conda-forge/linux-64/micromamba-2.10.0-0.tar.bz2 \
    | tar -xj -C "$PREFIX" bin/micromamba
fi
export MAMBA_ROOT_PREFIX="$PREFIX/root"
if [ ! -x "$PREFIX/envs/nuc/bin/njoy" ]; then
  "$PREFIX/bin/micromamba" create -y -q -p "$PREFIX/envs/nuc" -c conda-forge \
    python=3.12 njoy2016 "openmc=0.16.0=nodagmc_nompi*" pandas pyyaml requests pint pytest
fi
"$PREFIX/envs/nuc/bin/pip" install -q -e "$HERE"
echo "Done. Use: export PATH=$PREFIX/envs/nuc/bin:\$PATH; htfbr-data status"
