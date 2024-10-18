#!/usr/bin/env bash

if ! command -v podman &> /dev/null
then
    echo "Podman is not installed, install it to use this script."
    exit 1
fi

function is_yes {
    case $(echo "$1" | tr '[:upper:]' '[:lower:]') in
        y|yes) return 0;;
        *) return 1;;
    esac
}

# Define image configurations
declare -A image_configs=(
    ["securecore"]="Server"
    ["securecore-zfs"]="Server"
    ["silverblue"]="Silverblue:asus"
    ["kinoite"]="Kinoite:asus"
    ["sericea"]="Sericea"
    ["wayblue-wayfire"]="Sericea"
    ["wayblue-sway"]="Sericea"
    ["wayblue-river"]="Sericea"
    ["wayblue-hyprland"]="Sericea"
    ["cinnamon"]="Silverblue"
    ["cosmic"]="Kinoite"
)

image_name=""
additional_params=""
variant=""

# Determine if it's a server or desktop
read -p "Is this for a server? (yes/No): " is_server
if is_yes "$is_server"; then
    read -p "Do you need ZFS support? (yes/No): " use_zfs
    image_name=$(is_yes "$use_zfs" && echo "securecore-zfs" || echo "securecore")
    variant=${image_configs[$image_name]}
else
    # For desktops, present all non-server options
    desktop_options=($(for key in "${!image_configs[@]}"; do [[ $key != server* ]] && echo "$key"; done | sort))
    
    echo "Select a desktop:"
    select opt in "${desktop_options[@]}"; do
        if [[ " ${desktop_options[@]} " =~ " ${opt} " ]]; then
            image_name=$opt
            IFS=':' read -r variant options <<< "${image_configs[$opt]}"
            break
        else
            echo "Invalid option"
        fi
    done
    
    if [[ $options == *"asus"* ]]; then
        read -p "Do you use an Asus laptop? (yes/No): " is_asus
        is_yes "$is_asus" && additional_params+="-asus"
    fi
fi

# Ask about Nvidia for all options
read -p "Do you use Nvidia? (yes/No): " use_nvidia
is_yes "$use_nvidia" && additional_params+="-nvidia" || additional_params+="-main"

# Ask about user namespaces for all options
read -p "Do you need user namespaces? (yes/No): " use_userns
is_yes "$use_userns" && additional_params+="-userns"

image_name+="$additional_params-hardened"

command="sudo podman run --rm --privileged --volume .:/build-container-installer/build ghcr.io/jasonn3/build-container-installer:latest IMAGE_REPO=ghcr.io/secureblue IMAGE_NAME=$image_name VERSION=41 IMAGE_TAG=latest VARIANT=$variant"

echo "Command to execute:"
echo "$command"
echo ""

read -p "Generate this ISO? (yes/No): " generate_iso
if is_yes "$generate_iso"; then
    $command
    mv deploy.iso $image_name.iso
    mv deploy.iso-CHECKSUM $image_name.iso-CHECKSUM
    sed -i "s/deploy.iso/$image_name.iso/" "$image_name.iso-CHECKSUM"
fi
