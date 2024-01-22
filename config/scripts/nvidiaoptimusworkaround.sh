#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# applies workaround for known issue with optimus laptops for GNOME and Cinnamon
# https://gitlab.gnome.org/GNOME/mutter/-/issues/2969
echo "__EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json" >> /usr/etc/environment
