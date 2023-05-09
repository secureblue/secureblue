#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# Helper functions.
get_yaml_array() {
    mapfile -t "$1" < <(yq "$2" < /usr/etc/ublue-recipe.yml)
}

# Add custom repos.
get_yaml_array repos '.extrarepos[]'
if [[ ${#repos[@]} -gt 0 ]]; then
    echo "-- Adding repos defined in recipe.yml --"
    for repo in "${repos[@]}"; do
        wget "$repo" -P /etc/yum.repos.d/
    done
    echo "---"
fi

# Run scripts.
get_yaml_array buildscripts '.scripts[]'
if [[ ${#buildscripts[@]} -gt 0 ]]; then
    echo "-- Running scripts defined in recipe.yml --"
    for script in "${buildscripts[@]}"; do
        echo "Running: ${script}"
        /tmp/scripts/"$script"
    done
    echo "---"
fi

# Remove the default firefox (from fedora) in favor of the flatpak.
rpm-ostree override remove firefox firefox-langpacks

# Install RPMs.
get_yaml_array install_rpms '.rpms[]'
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
    yq -i '.screens.applications.values.groups.Custom.description = "Flatpaks defined by the image maintainer"' /usr/etc/yafti.yml
    yq -i '.screens.applications.values.groups.Custom.default = true' /usr/etc/yafti.yml
    for pkg in "${flatpaks[@]}"; do
        echo "Adding to yafti: ${pkg}"
        yq -i ".screens.applications.values.groups.Custom.packages += [{\"$pkg\": \"$pkg\"}]" /usr/etc/yafti.yml
    done
    echo "---"
fi
