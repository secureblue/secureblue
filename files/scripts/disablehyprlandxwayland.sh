#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail


echo "

xwayland {
  enabled = false
}

" > /usr/share/hyprland/hyprland.conf