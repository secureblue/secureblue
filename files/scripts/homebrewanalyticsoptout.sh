#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# https://docs.brew.sh/Analytics
echo "

HOMEBREW_NO_ANALYTICS=1

" >> /etc/environment
