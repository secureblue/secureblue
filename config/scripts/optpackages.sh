#!/usr/bin/env bash
set -oue pipefail

RECIPE_FILE="/usr/share/ublue-os/recipe.yml"
get_yaml_array() {
    mapfile -t "${1}" < <(yq -- "${2}" "${RECIPE_FILE}")
}

# Create symlinks to fix packages that create directories in /opt
get_yaml_array optpackages '.rpm.optfix[]'
if [[ ${#optpackages[@]} -gt 0 ]]; then
    echo "-- Creating symlinks to fix packages that install to /opt --"
    # Create symlink for /opt to /var/opt since it is not created in the image yet
    mkdir -p "/var/opt"
    ln -s "/var/opt"  "/opt"
    # Create symlinks for each directory specified in recipe.yml
    for optpackage in "${optpackages[@]}"; do
        optpackage="${optpackage%\"}"
        optpackage="${optpackage#\"}"
        mkdir -p "/usr/lib/opt/${optpackage}"
        ln -s "../../usr/lib/opt/${optpackage}" "/var/opt/${optpackage}"
        echo "Created symlinks for ${optpackage}"
    done
    echo "---"
fi