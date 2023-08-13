#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

get_yaml_array RUN '.run[]' "$1"

cd "$CONFIG_DIRECTORY/scripts"

pwd

for CMD in "${RUN[@]}"; do
    echo "Running command: $CMD"
    $CMD
done