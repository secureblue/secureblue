#!/usr/bin/bash
# shellcheck disable=SC2154
########
## Function to create a distrobox with standardized args
########
## Create a distrobox using default fedora:latest, name the box "my-fedora-box" and give it a custom homedir
# Distrobox "fedora:latest" "my-fedora-box" "$HOME/.var/containers/fedora-box"
## Create a debian toolbox distrobox named debian-unstable
# Distrobox "quay.io/toolbx-images/debian-toolbox:unstable" "debian-unstable"
## Create an ubuntu distrobox named someubuntubox with no custom homedir and unshare network namespace
## ($3 is required if supplying extra args, using "" makes the function skip it)
# Distrobox "ubuntu:latest" "someubuntubox" "" --unshare-ns
function Distrobox (){
    IMAGE="$1"
    NAME="$2"
    HOMEDIR=""
    # If custom home directory is supplied
    if [ -n "$3" ]; then
        HOMEDIR="$3"
    fi

    # If a custom home directory is not specified
    if [ -z "$HOMEDIR" ]; then
        distrobox create --nvidia -Y --image "$IMAGE" -n "$NAME" "${@:3}"
    else
        # Make the custom homedir path if it does not exist
        if [ ! -d "$HOMEDIR" ]; then
            mkdir -p "$HOMEDIR"
        fi
        # Create distrobox with custom home path
        distrobox create --nvidia -Y --image "$IMAGE" -n "$NAME" -H "$HOMEDIR" "${@:4}"
    fi
}

########
## Function to assemble pre-defined distrobox containers from manifest files
########
## Assemble all containers defined in an ini file without confirmation
# Assemble noconfirmcreate "/etc/distrobox/distrobox.ini"
# Assemble noconfirmcreate "" ALL
## Assemble ubuntu from default ini manifest, with confirmation
# Assemble confirm "" ubuntu
## Remove a container defined in the default ini manifest
# Assemble rm "" ubuntu
function Assemble(){
    # Set defaults
    ACTION="create"
    FILE="/etc/distrobox/distrobox.ini"
    NAME=""

    # If an action is provided
    if [ -n "$1" ]; then
        # Set ACTION to the action specified
        # and remove "noconfirm" from $1 when assigning it to ACTION
        ACTION="${1/noconfirm/}"
    fi

    # If a filename is provided
    if [ -n "$2" ]; then
        # Set FILE to the provided filename
        FILE="$2"
    fi

    # If container name is ALL
    if [ "$3" == "ALL" ] || [ -z "$3" ]; then
        if [[ ! "$1" =~ ^noconfirm ]]; then
            # Ask user if they REALLY want to assemble all the containers
            echo -e "${b}WARNING${n}: This will assemble and ${u}replace${n}\nALL containers defined in ${b}$FILE${n}."
            CONFIRM=$(Confirm "Are you sure you want to do this?")
            if [ "$CONFIRM" == "1" ]; then
                echo "Aborting..."
                return 1
            fi
        fi
        # Run the distrobox assemble command
        distrobox assemble "$ACTION" --file "$FILE" --replace
        return $?
    else
        # Set distrobox name to provided name
        NAME="$3"
    fi
    
    # If we do not want confirmations
    if [[ ! "$1" =~ ^noconfirm ]]; then
        # Ask the user if they really want to replace $NAME container
        echo -e "${b}WARNING${n}: This will assemble and ${u}replace${n} the container ${b}$NAME${n}\nwith the one defined in ${b}$FILE${n}."
        CONFIRM=$(Confirm "Are you sure you want to do this?")
        if [ "$CONFIRM" == "1" ]; then
            echo "Aborting..."
            return 1
        fi
    fi

    # Run the distrobox assemble command
    distrobox assemble "$ACTION" --file "$FILE" --name "$NAME" --replace
}

########
## Function to parse a distrobox.ini file and make a selectable list from it
########
## Parse a distrobox.ini manifest and let user select which container to setup
# AssembleList "$HOME/distrobox.ini" create
## Parse a distrobox.ini manifest and create ubuntu container without confirmation
# AssembleList "$HOME/distrobox.ini" noconfirmcreate ubuntu
function AssembleList (){
    # Set defaults
    FILE="$1"
    ACTION="create"
    CHOICE="prompt"

    # If an ACTION is supplied
    if [ -n "$2" ]; then
        # Replace default action
        ACTION="$2"
    fi
    
    # If a CHOICE is predefined
    if [ -n "$3" ]; then
        # Replace default choice
        CHOICE="$3"
    fi

    # If the choice is "prompt" then ask user what container they want
    if [ "$CHOICE" == "prompt" ]; then
        CONTAINERS=$(grep -P "\[.+\]" "$FILE" | sed -E 's/\[(.+)\]/\1/')
        echo "${b}Pre-defined Containers${n}"
        echo "Please select a container to create"
        # Disable an irrelevant shellscheck for next line as we want word splitting
        # shellcheck disable=SC2086
        CHOICE=$(Choose ALL $CONTAINERS)
    fi

    # If choice is not empty by now (will be empty if escaped from Choice function)
    if [ -n "$CHOICE" ]; then
        # Assemble the selected container
        Assemble "$ACTION" "$FILE" "$CHOICE"
    fi
}
