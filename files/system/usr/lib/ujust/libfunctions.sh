#!/usr/bin/bash
# shellcheck disable=SC2154
########
## Useful functions we use a lot, if you want to use them, source libjust.sh
## As it depends on libformatting.sh and libcolors.sh
## They are not imported here to avoid attempting to redeclare readonly vars.
########

########
## Function to generate a choice selection and return the selected choice
########
# CHOICE=$(Choice option1 option2 "option 3")
# *user selects "option 3"*
# echo "$CHOICE" will return "option 3"
function Choose (){
    CHOICE=$(ugum choose "$@")
    echo "$CHOICE"
}

########
## Function to generate a confirm dialog and return the selected choice
########
# CHOICE=$(Confirm "Are you sure you want to do this?")
# *user selects "No"*
# echo "$CHOICE" will return "1"
# 0 = Yes
# 1 = No
function Confirm (){
    ugum confirm "$@"
    echo $?
}
