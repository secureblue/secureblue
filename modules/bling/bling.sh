#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

get_yaml_array INSTALL '.install[]' "$1"

export BLING_DIRECTORY="/tmp/bling"

cd "/tmp/modules/bling/installers"

find "$PWD" -type f -exec chmod +x {} \;

for ITEM in "${INSTALL[@]}"; do
    echo "Pulling from bling: $ITEM"
    eval "$PWD/${ITEM%$'\n'}.sh"
done