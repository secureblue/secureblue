#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

FIRSTBOOT_DATA="/usr/share/ublue-os/firstboot"
FIRSTBOOT_LINK="/usr/etc/profile.d/ublue-firstboot.sh"

echo "Installing python3-pip and libadwaita"
rpm-ostree install python3-pip libadwaita

echo "Installing and enabling yafti"
pip install --prefix=/usr yafti

# Create symlink to our profile script, which creates the per-user "autorun yafti" links.
mkdir -p "$(dirname "${FIRSTBOOT_LINK}")"
ln -s "${FIRSTBOOT_DATA}/launcher/login-profile.sh" "${FIRSTBOOT_LINK}"

YAFTI_FILE="$FIRSTBOOT_DATA/yafti.yml"

get_yaml_array FLATPAKS '.custom-flatpaks[]' "$1"
if [[ ${#FLATPAKS[@]} -gt 0 ]]; then
    echo "Adding Flatpaks to yafti.yml"
    yq -i '.screens.applications.values.groups.Custom.description = "Flatpaks suggested by the image maintainer."' "${YAFTI_FILE}"
    yq -i '.screens.applications.values.groups.Custom.default = true' "${YAFTI_FILE}"

    for pkg in "${FLATPAKS[@]}"; do
        echo "Adding to yafti: ${pkg}"
        yq -i ".screens.applications.values.groups.Custom.packages += [$pkg]" "${YAFTI_FILE}"
    done
fi