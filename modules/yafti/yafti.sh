#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

YAFTI_FILE="/usr/share/ublue-os/firstboot/yafti.yml"

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