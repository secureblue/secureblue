#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "Disabling avahi-daemon"
systemctl disable avahi-daemon
systemctl mask avahi-daemon
