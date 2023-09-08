#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# Pull in repos
get_yaml_array REPOS '.repos[]' "$1"
if [[ ${#REPOS[@]} -gt 0 ]]; then
    echo "Adding repositories"
    for REPO in "${REPOS[@]}"; do
        REPO="${REPO//%OS_VERSION%/${OS_VERSION}}"
        wget "${REPO//[$'\t\r\n ']}" -P "/etc/yum.repos.d/"
    done
fi

# Create symlinks to fix packages that create directories in /opt
get_yaml_array OPTFIX '.optfix[]' "$1"
if [[ ${#OPTFIX[@]} -gt 0 ]]; then
    echo "Creating symlinks to fix packages that install to /opt"
    # Create symlink for /opt to /var/opt since it is not created in the image yet
    mkdir -p "/var/opt"
    ln -s "/var/opt"  "/opt"
    # Create symlinks for each directory specified in recipe.yml
    for OPTPKG in "${OPTFIX[@]}"; do
        OPTPKG="${OPTPKG%\"}"
        OPTPKG="${OPTPKG#\"}"
        OPTPKG=$(printf "$OPTPKG")
        mkdir -p "/usr/lib/opt/${OPTPKG}"
        ln -s "../../usr/lib/opt/${OPTPKG}" "/var/opt/${OPTPKG}"
        echo "Created symlinks for ${OPTPKG}"
    done
fi

get_yaml_array INSTALL '.install[]' "$1"
get_yaml_array REMOVE '.remove[]' "$1"

# The installation is done with some wordsplitting hacks
# because of errors when doing array destructuring at the installation step.
# This is different from other ublue projects and could be investigated further.
INSTALL_STR=$(echo "${INSTALL[*]}" | tr -d '\n')
REMOVE_STR=$(echo "${REMOVE[*]}" | tr -d '\n')

# Install and remove RPM packages
if [[ ${#INSTALL[@]} -gt 0 && ${#REMOVE[@]} -gt 0 ]]; then
    echo "Installing & Removing RPMs"
    echo "Installing: ${INSTALL_STR[*]}"
    echo "Removing: ${REMOVE_STR[*]}"
    # Doing both actions in one command allows for replacing required packages with alternatives
    rpm-ostree override remove ${REMOVE_STR[@]} $(printf -- "--install=%s " ${INSTALL_STR[@]})
elif [[ ${#INSTALL[@]} -gt 0 ]]; then
    echo "Installing RPMs"
    echo "Installing: ${INSTALL_STR[*]}"
    rpm-ostree install ${INSTALL_STR[@]}
elif [[ ${#INSTALL[@]} -gt 0 ]]; then
    echo "Removing RPMs"
    echo "Removing: ${REMOVE_STR[*]}"
    rpm-ostree override remove ${REMOVE_STR[@]}
fi
