#!/usr/bin/env bash

set -oue pipefail

echo "X-GNOME-Autostart-enabled=false" >> /etc/xdg/autostart/sealertauto.desktop
