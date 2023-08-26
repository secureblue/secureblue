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
    echo "Installing: ${INSTALL[*]}"
    rpm-ostree install "${INSTALL[@]}"
fi

get_yaml_array REMOVE '.remove[]' "$1"
if [[ ${#REMOVE[@]} -gt 0 ]]; then
    echo "Removing RPMs"
    echo "Removing: ${REMOVE[*]}"
    rpm-ostree override remove "${REMOVE[@]}"
fi