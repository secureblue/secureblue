#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# Helper functions.
RECIPE_FILE="/usr/share/ublue-os/recipe.yml"
YAFTI_FILE="/usr/share/ublue-os/firstboot/yafti.yml"
get_yaml_array() {
    mapfile -t "$1" < <(yq -- "$2" "$RECIPE_FILE")
}
get_yaml_string() {
    yq -- "$1" "$RECIPE_FILE"
}

# Automatically determine which Fedora version we're building.
FEDORA_VERSION="$(cat /usr/lib/os-release | grep '^VERSION_ID=' | head -1 | sed 's,^VERSION_ID=,,')"

# Read configuration variables.
base_image="$(get_yaml_string '.base-image')"

# Welcome.
echo "Building custom Fedora ${FEDORA_VERSION} from image: \"${base_image}\"."

# Add custom repos.
get_yaml_array repos '.rpm.repos[]'
if [[ ${#repos[@]} -gt 0 ]]; then
    echo "-- Adding repos defined in recipe.yml --"
    for repo in "${repos[@]}"; do
        repo="${repo//%FEDORA_VERSION%/${FEDORA_VERSION}}"
        wget "$repo" -P /etc/yum.repos.d/
    done
    echo "---"
fi

# Run "pre" scripts.
run_scripts() {
    script_mode="$1"
    get_yaml_array buildscripts ".scripts.${script_mode}[]"
    if [[ ${#buildscripts[@]} -gt 0 ]]; then
        echo "-- Running [${script_mode}] scripts defined in recipe.yml --"
        for script in "${buildscripts[@]}"; do
            echo "Running [${script_mode}]: ${script}"
            /tmp/scripts/"$script" "${script_mode}"
        done
        echo "---"
    fi
}
run_scripts "pre"

# Remove RPMs.
get_yaml_array remove_rpms '.rpm.remove[]'
if [[ ${#remove_rpms[@]} -gt 0 ]]; then
    echo "-- Removing RPMs defined in recipe.yml --"
    echo "Removing: ${remove_rpms[@]}"
    rpm-ostree override remove "${remove_rpms[@]}"
    echo "---"
fi

# Install RPMs.
get_yaml_array install_rpms '.rpm.install[]'
if [[ ${#install_rpms[@]} -gt 0 ]]; then
    echo "-- Installing RPMs defined in recipe.yml --"
    echo "Installing: ${install_rpms[@]}"
    rpm-ostree install "${install_rpms[@]}"
    echo "---"
fi

# Install yafti to install flatpaks on first boot, https://github.com/ublue-os/yafti.
pip install --prefix=/usr yafti

# Add a new yafti "package group" called Custom, for the packages defined in recipe.yml.
# Only adds the package group if some flatpaks are defined in the recipe.
get_yaml_array flatpaks '.flatpaks[]'
if [[ ${#flatpaks[@]} -gt 0 ]]; then
    echo "-- yafti: Adding Flatpaks defined in recipe.yml --"
    yq -i '.screens.applications.values.groups.Custom.description = "Flatpaks defined by the image maintainer"' "$YAFTI_FILE"
    yq -i '.screens.applications.values.groups.Custom.default = true' "$YAFTI_FILE"
    for pkg in "${flatpaks[@]}"; do
        echo "Adding to yafti: ${pkg}"
        yq -i ".screens.applications.values.groups.Custom.packages += [{\"$pkg\": \"$pkg\"}]" "$YAFTI_FILE"
    done
    echo "---"
fi

# Run "post" scripts.
run_scripts "post"
