#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

patch /usr/share/ublue-os/just/05-brew.just < enable-wheelless-brew-installation.patch 
patch /usr/share/ublue-os/just/15-luks.just < use-pkexec-in-luks-just.patch
patch /usr/share/ublue-os/just/40-nvidia.just < remove-unusable-just-command.patch
