#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

get_yaml_array SCRIPTS '.scripts[]' "$1"

cd "$CONFIG_DIRECTORY/scripts"

# Make every script executable
find "$PWD" -type f -exec chmod +x {} \;

for SCRIPT in "${SCRIPTS[@]}"; do
    echo "Running script $SCRIPT"
    eval "$PWD/$SCRIPT"
done