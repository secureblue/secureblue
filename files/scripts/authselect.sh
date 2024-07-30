#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "Selecting the secureblue authselect profile"

authselect select custom/secureblue
