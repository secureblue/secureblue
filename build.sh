#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

export CONFIG_DIRECTORY="/usr/share/ublue-os/startingpoint"
RECIPE_FILE="$CONFIG_DIRECTORY/$RECIPE"
MODULE_DIRECTORY="/tmp/modules"

# https://mikefarah.gitbook.io/yq/usage/tips-and-tricks#yq-in-a-bash-loop
get_yaml_array() {
    # creates array $1 with content at key $2 from $3 
    readarray "$1" < <(echo "$3" | yq -o=j -I=0 "$2" )
}
export -f get_yaml_array # this makes the function available to all modules

# Automatically determine which Fedora version we're building.
export FEDORA_VERSION="$(grep -Po '(?<=VERSION_ID=)\d+' /usr/lib/os-release)"

# Read configuration variables.
BASE_IMAGE="$(yq '.base-image' "$RECIPE_FILE")"
IMAGE_NAME="$(yq '.name' "$RECIPE_FILE")"

# Welcome.
echo "Building $IMAGE_NAME from Fedora $FEDORA_VERSION ($BASE_IMAGE)."

# Run each module
readarray MODULES < <(yq -o=j -I=0 '.modules[]' "$RECIPE_FILE" )

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