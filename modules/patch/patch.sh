#!/usr/bin/env bash

set -euo pipefail
shopt -s nullglob

get_json_array PATCHES 'try .["patches"][]' "$1"
PATCH_DIR="$CONFIG_DIRECTORY/patches"
readonly PATCHES PATCH_DIR

main() {
    local p
    for p in "${PATCHES[@]}"; do
        patch --batch --silent --forward --no-backup-if-mismatch \
              --directory=/ --strip=1 < "$PATCH_DIR/$p"
    done
}

main "$@"
