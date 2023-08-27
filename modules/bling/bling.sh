#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

get_yaml_array INSTALL '.install[]' "$1"

export BLING_DIRECTORY="/tmp/bling"

cd "/tmp/modules/bling/installers"

# Make every bling installer executable
find "$PWD" -type f -exec chmod +x {} \;

for ITEM in "${INSTALL[@]}"; do
    echo "Pulling from bling: $ITEM"
    # The trainling newline from $ITEM is removed
    eval "$PWD/${ITEM%$'\n'}.sh"
done