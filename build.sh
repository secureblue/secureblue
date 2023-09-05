#!/usr/bin/env bash

# This script executes the modules in order.
# If you have some custom commands you need to run, you should not put them here.
# Instead, you should probably include them as custom scripts.
# Editing this file directly is an unsupported configuration.

# Tell build process to exit if there are any errors.
set -oue pipefail

export CONFIG_DIRECTORY="/tmp/config"
RECIPE_FILE="$CONFIG_DIRECTORY/$RECIPE"
MODULE_DIRECTORY="/tmp/modules"

# https://mikefarah.gitbook.io/yq/usage/tips-and-tricks#yq-in-a-bash-loop
get_yaml_array() {
    # creates array $1 with content at key $2 from $3 
    readarray "$1" < <(echo "$3" | yq -I=0 "$2")
}
export -f get_yaml_array # this makes the function available to all modules

# Declare dynamically generated variables as exported
declare -x IMAGE_NAME BASE_IMAGE OS_VERSION

# Read configuration variables.
BASE_IMAGE="$(yq '.base-image' "$RECIPE_FILE")"
IMAGE_NAME="$(yq '.name' "$RECIPE_FILE")"

# Automatically determine which Fedora version we're building.
OS_VERSION="$(grep -Po '(?<=VERSION_ID=)\d+' /usr/lib/os-release)"

# Welcome.
echo "Building $IMAGE_NAME from $BASE_IMAGE:$OS_VERSION."

# Run each module
readarray MODULES < <(yq -o=j -I=0 '.modules[]' "$RECIPE_FILE" )

for MODULE in "${MODULES[@]}"; do
    TYPE=$(echo "$MODULE" | yq '.type')
    if [[ "$TYPE" != "null" ]]; then
        # If type is found, that means that the module config
        # has been declared inline, and thus is safe to pass to the module
        echo "=== Launching module of type: $TYPE ==="
        bash "$MODULE_DIRECTORY/$TYPE/$TYPE.sh" "$MODULE"
    else
        # If the type is not found, that means that the module config
        # is in a separate file, and has to be read from it
        FILE=$(echo "$MODULE" | yq '.from-file')
        MODULE_CONFIG=$(yq -o=j -I=0 '.' "$CONFIG_DIRECTORY/$FILE")

        TYPE=$(echo "$MODULE_CONFIG" | yq '.type')
        echo "=== Launching module of type: $TYPE ==="
        bash "$MODULE_DIRECTORY/$TYPE/$TYPE.sh" "$MODULE_CONFIG"
    fi
    echo "======"
done
