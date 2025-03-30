#!/usr/bin/env bash

set -oue pipefail

echo "Disabling avahi-daemon"
systemctl disable avahi-daemon
systemctl mask avahi-daemon
