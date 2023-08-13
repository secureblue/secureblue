#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

CONFIG_DIRECTORY="/usr/share/ublue-os/startingpoint/"
RECIPE_FILE="$CONFIG_DIRECTORY/$RECIPE"
MODULE_DIRECTORY="/tmp/modules/"

# https://mikefarah.gitbook.io/yq/usage/tips-and-tricks#yq-in-a-bash-loop
get_yaml_array() {
    readarray "$1" < <(yq -o=j -I=0 "$2" "$RECIPE_FILE" )
}

# Automatically determine which Fedora version we're building.
FEDORA_VERSION="$(grep -Po '(?<=VERSION_ID=)\d+' /usr/lib/os-release)"

# Read configuration variables.
BASE_IMAGE="$(yq '.base-image' "$RECIPE_FILE")"
IMAGE_NAME="$(yq '.name' "$RECIPE_FILE")"

# Welcome.
echo "Building $IMAGE_NAME from Fedora $FEDORA_VERSION ($BASE_IMAGE)."

# Run each module
get_yaml_array MODULES '.modules[]'

for MODULE in "${MODULES[@]}"; do
    TYPE=$(echo "$MODULE" | yq '.type')
    if [[ "$TYPE" != "null" ]]; then
        echo "Launching module of type: $TYPE"
        bash "$MODULE_DIRECTORY/$TYPE/$TYPE.sh" "$MODULE"
    else
        FILE=$(echo "$MODULE" | yq '.from-file')
        MODULE_CONFIG=$(yq -o=j -I=0 '.' "$CONFIG_DIRECTORY/$FILE")

        TYPE=$(echo "$MODULE_CONFIG" | yq '.type')
        echo "Launching module of type: $TYPE"
        bash "$MODULE_DIRECTORY/$TYPE/$TYPE.sh" "$MODULE_CONFIG"
    fi
done