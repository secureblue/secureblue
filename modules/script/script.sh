#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

cd "$CONFIG_DIRECTORY/scripts"

get_yaml_array RUN '.run[]'
for CMD in "${RUN[@]}"; do
    echo "Running command: $CMD"
    $CMD
done