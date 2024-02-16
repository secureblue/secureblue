#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# applies workaround for known issue with optimus laptops for GNOME and Cinnamon
# https://gitlab.gnome.org/GNOME/mutter/-/issues/2969#note_1872558
mv /usr/share/glvnd/egl_vendor.d/10_nvidia.json /usr/share/glvnd/egl_vendor.d/90_nvidia.json
