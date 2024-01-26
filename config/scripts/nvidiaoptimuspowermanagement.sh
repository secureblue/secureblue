#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "
# Enable Fine-Grained DynamicPowerManagement
# https://download.nvidia.com/XFree86/Linux-x86_64/545.29.06/README/dynamicpowermanagement.html
options nvidia NVreg_DynamicPowerManagement=0x02
" >> /usr/etc/modprobe.d/nvidia.conf
