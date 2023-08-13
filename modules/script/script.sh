#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

readarray RUN < <(yq -o=j -I=0 '.run[]' "$1" )

cd "$CONFIG_DIRECTORY/scripts"

for CMD in "${RUN[@]}"; do
    echo "Running command: $CMD"
    $CMD
done