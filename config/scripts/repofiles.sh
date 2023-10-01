#!/usr/bin/env bash
set -oue pipefail

RECIPE_FILE="/usr/share/ublue-os/recipe.yml"
get_yaml_array() {
    mapfile -t "${1}" < <(yq -- "${2}" "${RECIPE_FILE}")
}

# Add repo files.
get_yaml_array repos '.rpm.repo-files[]'
if [[ ${#repos[@]} -gt 0 ]]; then
    echo "-- Adding .repo files defined in recipe.yml --"
    for repo in "${repos[@]}"; do
        wget "${repo}" -P "/etc/yum.repos.d/"
    done
    echo "---"
fi