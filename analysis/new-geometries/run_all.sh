#!/bin/bash
# Wait for the OpenMC library, then run the neutronics cases and the finite-core check (one stream).
export PATH=/opt/mamba/envs/nuc/bin:$PATH
cd "$(dirname "$0")"
until [ -f ../../data/openmc/cross_sections.xml ]; do sleep 60; done
python neutronics.py "$@"
