#!/usr/bin/env bash

set -oue pipefail

echo "Disabling the sssd daemons"
systemctl disable sssd
systemctl mask sssd

systemctl disable sssd-kcm
systemctl mask sssd-kcm