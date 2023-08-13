#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# Absolute path to recipe file
RECIPE_FILE="/usr/share/ublue-os/startingpoint/${RECIPE}"

# https://mikefarah.gitbook.io/yq/usage/tips-and-tricks#yq-in-a-bash-loop
get_yaml_array() {
    readarray "$1" < <(yq -o=j -I=0 "$2" "$RECIPE_FILE" )
}

get_yaml_string() {
    yq -- "${1}" "${RECIPE_FILE}"
}

# Automatically determine which Fedora version we're building.
FEDORA_VERSION="$(grep -Po '(?<=VERSION_ID=)\d+' /usr/lib/os-release)"

# Read configuration variables.
BASE_IMAGE="$(get_yaml_string '.base-image')"
IMAGE_NAME="$(get_yaml_string '.name')"

# Welcome.
echo "Building $IMAGE_NAME from Fedora $FEDORA_VERSION ($BASE_IMAGE)."

# Run each module
get_yaml_array MODULES '.modules[]'

for module in "${MODULES[@]}"; do
    TYPE=$(echo "$module" | yq '.type')

    echo "Launching module of type: $TYPE"
done