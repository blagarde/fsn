#!/usr/bin/env bash
# Wait for the targets run to finish, then process every remaining evaluation in ENDF/B-VIII.0.
cd /home/user/htfbr-data
export PATH=/opt/mamba/envs/nuc/bin:$PATH
while pgrep -f "htfbr-data endf$" >/dev/null; do sleep 30; done
htfbr-data endf --all --skip-done > reports/endf_full_library.log 2>&1
htfbr-data check >> reports/endf_full_library.log 2>&1
