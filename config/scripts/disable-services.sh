#!/usr/bin/env bash

# Tell this script to exit if there are any errors.
set -oue pipefail

sudo systemctl stop cups
sudo systemctl disable cups
sudo systemctl mask cups.socket

sudo systemctl daemon-reload
