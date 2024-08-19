#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

patch /usr/share/ublue-os/just/05-brew.just < enable-wheelless-brew-installation.patch 

