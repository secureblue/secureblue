#!/usr/bin/env bash

if ! command -v podman &> /dev/null
then
    echo "Podman is not installed, install it to use this script."
fi

function is_yes {
    case $(echo "$1" | tr '[:upper:]' '[:lower:]') in
        y|yes) return 0;;
        *) return 1;;
    esac
}

desktop_options=("kinoite" "cinnamon" "bluefin" "silverblue" "sericea" "wayblue-wayfire" "wayblue-sway" "wayblue-river" "wayblue-hyprland")
desktop_options_asus=("silverblue" "kinoite")

image_name=""

read -p "Do you need user namespaces? (yes/No): " use_userns
read -p "Do you use an Asus laptop? (yes/No): " is_asus
read -p "Do you use Nvidia? (yes/No): " use_nvidia
if is_yes "$is_asus"; then
    echo "Select a desktop:"
    select opt in "${desktop_options_asus[@]}"; do
        case $opt in
            "silverblue")
                image_name+="silverblue"
                break;
                ;;
            "kinoite")
                image_name+="kinoite"
                break;
                ;;
            *) echo "Invalid option";;
        esac
    done

    image_name+="-asus"
    if is_yes "$use_nvidia"; then
        image_name+="-nvidia"
    fi
else
    read -p "Is this for a server? (yes/No): " is_server
    if is_yes "$is_server"; then
        image_name+="server"
    else 
        echo "Select a desktop:"
        select opt in "${desktop_options[@]}"; do
            case $opt in
                "silverblue")
                    image_name+="silverblue"
                    break;
                    ;;
                "kinoite")
                    image_name+="kinoite"
                    break;
                    ;;
                "cinnamon")
                    image_name+="cinnamon"
                    break;
                    ;;
                "sericea")
                    image_name+="sericea"
                    break;
                    ;;
                "bluefin")
                    image_name+="bluefin"
                    break;
                    ;;
                "wayblue-river")
                    image_name+="wayblue-river"
                    break;
                    ;;
                "wayblue-sway")
                    image_name+="wayblue-sway"
                    break;
                    ;;
                "wayblue-hyprland")
                    image_name+="wayblue-hyprland"
                    break;
                    ;;
                "wayblue-wayfire")
                    image_name+="wayblue-wayfire"
                    break;
                    ;;
                *) echo "Invalid option";;
            esac
        done
    fi

    if is_yes "$use_nvidia"; then
        image_name+="-nvidia"
    else
        image_name+="-main"
    fi
fi

if is_yes "$use_userns"; then
    image_name+="-userns"
fi

image_name+="-hardened"

command="sudo podman run --rm --privileged --volume .:/build-container-installer/build ghcr.io/jasonn3/build-container-installer:latest IMAGE_REPO=ghcr.io/secureblue IMAGE_NAME=$image_name VERSION=40 IMAGE_TAG=latest"

echo "Command to execute:"
echo "$command"
echo ""

read -p "Generate this ISO? (yes/No): " generate_iso
if is_yes "$generate_iso"; then
    $command
    mv deploy.iso $image_name.iso
    mv deploy.iso-CHECKSUM $image_name.iso-CHECKSUM
    sed -i 's/deploy.iso/$image_name.iso/' $image_name.iso-CHECKSUM
fi
