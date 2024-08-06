#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "Disabling sshd"
systemctl disable sshd
systemctl mask sshd
