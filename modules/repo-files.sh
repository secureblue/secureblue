#!/usr/bin/env bash
set -oue pipefail

# Add repo files.
get_yaml_array repos '.repos[]'
if [[ ${#repos[@]} -gt 0 ]]; then
    echo "-- Adding .repo files defined in recipe.yml --"
    for repo in "${repos[@]}"; do
        wget "${repo}" -P "/etc/yum.repos.d/"
    done
    echo "---"
fi