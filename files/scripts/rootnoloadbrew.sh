#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

PATCH_ARGS=("--forward" "--strip=1" "--no-backup-if-mismatch")

if [ -f /etc/profile.d/brew-bash-completions.sh ]; then
    patch /etc/profile.d/brew-bash-completions.sh "${PATCH_ARGS[@]}" < rootnoloadbrew.patch
fi

