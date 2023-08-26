#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

get_yaml_array REPOS '.repos[]' "$1"
if [[ ${#REPOS[@]} -gt 0 ]]; then
    echo "Adding repositories"
    for REPO in "${REPOS[@]}"; do
        REPO="${REPO//%OS_VERSION%/${OS_VERSION}}"
        wget "${REPO}" -P "/etc/yum.repos.d/"
    done
fi

get_yaml_array INSTALL '.install[]' "$1"
if [[ ${#INSTALL[@]} -gt 0 ]]; then
    echo "Installing RPMs"
    INSTALL_STR=$(echo "${INSTALL[*]}" | tr -d '\n')
    echo "Installing: $INSTALL_STR"
    rpm-ostree install "$INSTALL_STR"
fi

get_yaml_array REMOVE '.remove[]' "$1"
if [[ ${#REMOVE[@]} -gt 0 ]]; then
    echo "Removing RPMs"
    REMOVE_STR=$(echo "${REMOVE[*]}" | tr -d '\n')
    echo "Removing: $REMOVE"
    rpm-ostree override remove "$REMOVE_STR"
fi