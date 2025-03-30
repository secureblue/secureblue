#!/usr/bin/env bash

set -oue pipefail

echo "Disabling sshd"
systemctl disable sshd
systemctl mask sshd
