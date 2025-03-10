#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

PATCH_ARGS=("--forward" "--strip=1" "--no-backup-if-mismatch")

patch /etc/login.defs "${PATCH_ARGS[@]}" < hardenlogindefs.patch
