#!/usr/bin/bash
# shellcheck disable=SC2154
########
## Function to create a toolbox with standardized args
########
## Create a debian toolbox toolbox named debian-unstable
# Toolbox create "quay.io/toolbx-images/debian-toolbox:unstable" "debian-unstable"
## Create an ubuntu toolbox and provide an authfile to authenticate with the registry
# Toolbox create "ubuntu:22.04" --authfile "/path/to/file"
function Toolbox (){
    # Get the action we want to do
    local ACTION="$1"
    # Get the "image" argument, we use this as an abstraction layer
    # To decide if it is an image registry or a distro+release image argument
    local IMAGE="$2"

    # Define local variables
    local DISTRORELEASE

    # If the ACTION is "replace"
    if [ "$1" == "replace" ]; then
        # Set ACTION to create
        ACTION="create"

        # Remove old image before continuing
        toolbox rm --force "${@:3}" 
    fi

    # Check if $IMAGE is an image registry url
    if [[ "$IMAGE" =~ / ]]; then
        # Create toolbox based on image from registry
        toolbox "$ACTION" --image "$IMAGE" "${@:3}"
    else
        # Split IMAGE string into an array
        # shellcheck disable=SC2206
        DISTRORELEASE=(${IMAGE//:/ })
        # Create toolbox with distro and release args
        toolbox "$ACTION" --distro "${DISTRORELEASE[0]}" --release "${DISTRORELEASE[1]}" "${@:3}" 
    fi
}

########
## Function to assemble pre-defined toolbox containers from manifest files
########
## Assemble all containers defined in an ini file without confirmation
# ToolboxAssemble noconfirmcreate "/etc/toolbox/toolbox.ini"
# ToolboxAssemble noconfirmcreate "/etc/toolbox/toolbox.ini" ALL
## Assemble ubuntu from default ini manifest, with confirmation
# ToolboxAssemble confirm "/etc/toolbox/toolbox.ini" ubuntu-toolbox-22.04
## Remove a container defined in the default ini manifest
# ToolboxAssemble rm "/etc/toolbox/toolbox.ini" ubuntu-toolbox-22.04
function ToolboxAssemble (){
    # Set defaults
    local ACTION="create"
    local FILE="/etc/toolbox/toolbox.ini"
    local NAME=""

    # Define local variables
    local CONTAINERS
    local IMAGE
    local CONFIRM

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
        # Get all the containers
        CONTAINERS=$(grep -P "\[.+\]" "$FILE" | sed -E 's/\[(.+)\]/\1/')
        
        # Run the toolbox assemble command
        #toolbox assemble "$ACTION" --file "$FILE" --replace
        for CONTAINER in $CONTAINERS
        do
            # Get the image for the container
            IMAGE=$(grep -A1 -P "\[$CONTAINER\]" "$FILE" | grep "image" | sed 's/image=//')

            # Replace the container
            Toolbox replace "$IMAGE" "$CONTAINER"
        done
        return $?
    else
        # Set toolbox name to provided name
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

    # Get the image for the container
    IMAGE=$(grep -A1 -P "\[$NAME\]" "$FILE" | grep "image" | sed 's/image=//')

    # Replace the toolbox container
    Toolbox replace "$IMAGE" "$NAME"
}

########
## Function to parse a toolbox.ini file and make a selectable list from it
########
## Parse a toolbox.ini manifest and let user select which container to setup
# ToolboxAssembleList "$HOME/toolbox.ini" create
## Parse a toolbox.ini manifest and create ubuntu container without confirmation
# ToolboxAssembleList "$HOME/toolbox.ini" noconfirmcreate ubuntu-toolbox-22.04
function ToolboxAssembleList (){
    # Set defaults
    local FILE="$1"
    local ACTION="create"
    local CHOICE="prompt"

    # Define local variables
    local CONTAINERS

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
        # If ACTION is create
        if [ "$ACTION" == "create" ]; then
            ACTION="replace"
        fi
        # Assemble the selected container
        ToolboxAssemble "$ACTION" "$FILE" "$CHOICE"
    fi
}
