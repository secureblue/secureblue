#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# Helper functions.
RECIPE_FILE="/usr/share/ublue-os/recipe.yml"
get_yaml_array() {
    mapfile -t "${1}" < <(yq -- "${2}" "${RECIPE_FILE}")
}
get_yaml_string() {
    yq -- "${1}" "${RECIPE_FILE}"
}

# Automatically determine which Fedora version we're building.
FEDORA_VERSION="$(cat /usr/lib/os-release | grep -Po '(?<=VERSION_ID=)\d+')"

# Read configuration variables.
BASE_IMAGE="$(get_yaml_string '.base-image')"
YAFTI_ENABLED="$(get_yaml_string '.firstboot.yafti')"

# Welcome.
echo "Building custom Fedora ${FEDORA_VERSION} from image: \"${BASE_IMAGE}\"."

# Add custom repos.
get_yaml_array repos '.rpm.repos[]'
if [[ ${#repos[@]} -gt 0 ]]; then
    echo "-- Adding repos defined in recipe.yml --"
    for repo in "${repos[@]}"; do
        repo="${repo//%FEDORA_VERSION%/${FEDORA_VERSION}}"
        wget "${repo}" -P "/etc/yum.repos.d/"
    done
    echo "---"
fi

# Ensure that all script files are executable.
find /tmp/scripts -type f -exec chmod +x {} \;

# Run "pre" scripts.
run_scripts() {
    script_mode="$1"
    get_yaml_array buildscripts ".scripts.${script_mode}[]"
    if [[ ${#buildscripts[@]} -gt 0 ]]; then
        echo "-- Running [${script_mode}] scripts defined in recipe.yml --"
        for script in "${buildscripts[@]}"; do
            echo "Running [${script_mode}]: ${script}"
            "/tmp/scripts/${script}" "${script_mode}"
        done
        echo "---"
    fi
}
run_scripts "pre"

# Install RPMs.
get_yaml_array install_rpms '.rpm.install[]'
if [[ ${#install_rpms[@]} -gt 0 ]]; then
    echo "-- Installing RPMs defined in recipe.yml --"
    echo "Installing: ${install_rpms[@]}"
    rpm-ostree install "${install_rpms[@]}"
    echo "---"
fi

# Remove RPMs.
get_yaml_array remove_rpms '.rpm.remove[]'
if [[ ${#remove_rpms[@]} -gt 0 ]]; then
    echo "-- Removing RPMs defined in recipe.yml --"
    echo "Removing: ${remove_rpms[@]}"
    rpm-ostree override remove "${remove_rpms[@]}"
    echo "---"
fi

# Toggle yafti, which provides the "first boot" experience, https://github.com/ublue-os/yafti.
FIRSTBOOT_DATA="/usr/share/ublue-os/firstboot"
FIRSTBOOT_LINK="/usr/etc/profile.d/ublue-firstboot.sh"
if [[ "${YAFTI_ENABLED}" == "true" ]]; then
    echo "-- firstboot: Installing and enabling \"yafti\" --"
    pip install --prefix=/usr yafti
    # Create symlink to our profile script, which creates the per-user "autorun yafti" links.
    mkdir -p "$(dirname "${FIRSTBOOT_LINK}")"
    ln -s "${FIRSTBOOT_DATA}/launcher/login-profile.sh" "${FIRSTBOOT_LINK}"
else
    echo "-- firstboot: Removing all \"firstboot\" components --"
    # Removes the script symlink that creates the per-user autostart symlinks.
    # We must forcibly remove this here, in case it was added by an upstream image.
    rm -f "${FIRSTBOOT_LINK}"
    # Remove all of the launcher-scripts and yafti config, to de-clutter image and
    # ensure it can't run by accident due to lingering symlinks or upstream image.
    rm -rf "${FIRSTBOOT_DATA}"
fi

# Add a new yafti "package group" called Custom, for the packages defined in recipe.yml.
# Only adds the package group if yafti is enabled and Flatpaks are defined in the recipe.
if [[ "${YAFTI_ENABLED}" == "true" ]]; then
    YAFTI_FILE="${FIRSTBOOT_DATA}/yafti.yml"
    get_yaml_array flatpaks '.firstboot.flatpaks[]'
    if [[ ${#flatpaks[@]} -gt 0 ]]; then
        echo "-- yafti: Adding Flatpaks defined in recipe.yml --"
        yq -i '.screens.applications.values.groups.Custom.description = "Flatpaks suggested by the image maintainer."' "${YAFTI_FILE}"
        yq -i '.screens.applications.values.groups.Custom.default = true' "${YAFTI_FILE}"
        for pkg in "${flatpaks[@]}"; do
            echo "Adding to yafti: ${pkg}"
            yq -i ".screens.applications.values.groups.Custom.packages += [{\"${pkg}\": \"${pkg}\"}]" "${YAFTI_FILE}"
        done
        echo "---"
    fi
fi

# Run "post" scripts.
run_scripts "post"
