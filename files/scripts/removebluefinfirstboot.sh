#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

rm /etc/skel/.config/autostart/bluefin-firstboot.desktop
