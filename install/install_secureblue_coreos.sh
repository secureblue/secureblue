#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

if ! command -v rpm-ostree &> /dev/null
then
    echo "This script only runs on Fedora Atomic"
    exit 1
fi

version=$(rpm-ostree --version | grep -oP "Version: '\K[^']+" )
year=$(echo "$version" | cut -d '.' -f 1)
subversion=$(echo "$version" | cut -d '.' -f 2)


if [[ "$year" -lt 2024 || ( "$year" -eq 2024 && "$subversion" -lt 9 ) ]]; then
  echo "rpm-ostree is too old, please upgrade before running this script. Found version: $version"
  exit 1
else
  echo "rpm-ostree is 2024.9 or later, proceeding..."
fi

function is_yes {
    case $(echo "$1" | tr '[:upper:]' '[:lower:]') in
        y|yes) return 0;;
        *) return 1;;
    esac
}

image_name=""
additional_params=""

printf "%s\n\n" \
    "Welcome to the secureblue interactive installer!" \
    "After answering the following questions, your system will be rebased to secureblue."


if ! grep VARIANT=\"CoreOS\" /etc/os-release >/dev/null; then
    echo "The current operating system is based on Fedora Atomic."
    echo "Fedora Atomic and CoreOS use different partitioning schemes and are not compatible."
    echo "Refusing to proceed."
    exit 1
fi
read -rp "Do you need ZFS support? (yes/No): " use_zfs
image_name=$(is_yes "$use_zfs" && echo "securecore-zfs" || echo "securecore")


# Ask about Nvidia for all options
echo "Nvidia's proprietary drivers provide superior performance on Nvidia hardware."
read -rp "Do you want Nvidia proprietary drivers? (yes/No): " use_nvidia
if is_yes "$use_nvidia"; then
    additional_params+="-nvidia"
    echo "Nvidia's proprietary drivers with open source kernel modules are recommended for Turing or newer cards (GTX 16XX+)."
    read -rp "Do you want Nvidia's proprietary drivers with open source kernel modules? (Yes/no): " use_open
    use_open=${use_open:-y}
    is_yes "$use_open" && additional_params+="-open"
else
    additional_params+="-main"
fi

image_name+="$additional_params-hardened"

rebase_command="rpm-ostree rebase ostree-unverified-registry:ghcr.io/secureblue/$image_name:latest"

if rpm-ostree status | grep -q '●.*ghcr\.io/secureblue/'; then
    rebase_command="rpm-ostree rebase ostree-image-signed:docker://ghcr.io/secureblue/$image_name:latest"
else
    echo "Note: Automatic rebasing to the equivalent signed image will occur on first run."
fi

printf "Command to execute:\n%s\n\n" "$rebase_command"

read -rp "Proceed? (yes/No): " rebase_proceed
if is_yes "$rebase_proceed"; then
    eval "$rebase_command"
fi
