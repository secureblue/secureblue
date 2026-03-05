#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

if ! command -v rpm-ostree &> /dev/null
then
    echo "This script only runs on Fedora Atomic"
    exit 1
fi

function is_yes {
    case $(echo "$1" | tr '[:upper:]' '[:lower:]') in
        y|yes) return 0;;
        *) return 1;;
    esac
}

# Define image configurations
desktop_image_types=(
    "silverblue"
    "kinoite"
    "sericea"
    "cosmic"
)

image_name=""
additional_params=""

printf "%s\n\n" \
    "Welcome to the secureblue interactive installer!" \
    "After answering the following questions, your system will be rebased to secureblue."

# Determine if it's a server or desktop
read -rp "Is this for a CoreOS server? (yes/No): " is_server
if is_yes "$is_server"; then
    if ! grep VARIANT=\"CoreOS\" /etc/os-release >/dev/null; then
        echo "The current operating system is based on Fedora Atomic."
        echo "Fedora Atomic and CoreOS use different partitioning schemes and are not compatible."
        echo "Refusing to proceed."
        exit 1
    fi
    read -rp "Do you need ZFS support? (yes/No): " use_zfs
    image_name=$(is_yes "$use_zfs" && echo "securecore-zfs" || echo "securecore")
else
    if grep VARIANT=\"CoreOS\" /etc/os-release >/dev/null; then
        echo "The current operating system is based on CoreOS."
        echo "Fedora Atomic and CoreOS use different partitioning schemes and are not compatible."
        echo "Refusing to proceed."
        exit 1
    fi
    printf "%s\n" \
        "Select a desktop." \
        "Silverblue images are recommended." \
        "Sericea images are recommended for tiling WM users." \
        "Cosmic images are considered experimental."
    PS3=$'Enter your desktop choice: '
    select image_name in "${desktop_image_types[@]}"; do
        if [[ -n "$image_name" ]]; then        
            echo "Selected desktop: $image_name"
            break
        else
            echo "Invalid option, please select a valid number."
        fi
    done
fi

# Ask about Nvidia for all options
read -rp "Do you have Nvidia? (yes/No): " use_nvidia
if is_yes "$use_nvidia"; then
    additional_params+="-nvidia" 
    read -rp "Do you need Nvidia's open drivers? (yes/No): " use_open
    is_yes "$use_open" && additional_params+="-open"
else
    additional_params+="-main"
fi

image_name+="$additional_params-hardened"

rebase_command="rpm-ostree rebase ostree-unverified-registry:ghcr.io/secureblue/$image_name:latest"

if rpm-ostree status | grep -q '●.*ghcr\.io/secureblue/'; then
    full_ref=$(crane digest --full-ref "ghcr.io/secureblue/${image_name}:latest")
    slsa-verifier verify-image --source-uri "github.com/secureblue/secureblue" --source-branch "live" "${full_ref}"
    rebase_command="rpm-ostree rebase ostree-image-signed:docker://ghcr.io/secureblue/$image_name:latest"
else
    echo "Note: Automatic rebasing to the equivalent signed image will occur on first run."
fi

printf "Command to execute:\n%s\n\n" "$rebase_command"

read -rp "Proceed? (yes/No): " rebase_proceed
if is_yes "$rebase_proceed"; then
    eval "$rebase_command"
fi
