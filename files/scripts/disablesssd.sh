#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "Disabling the sssd daemons"
systemctl disable sssd
systemctl mask sssd

systemctl disable sssd-kcm
systemctl mask sssd-kcm