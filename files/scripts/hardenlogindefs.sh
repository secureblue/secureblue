#!/usr/bin/env bash

set -oue pipefail

PATCH_ARGS=("--forward" "--strip=1" "--no-backup-if-mismatch")

patch /etc/login.defs "${PATCH_ARGS[@]}" < hardenlogindefs.patch
