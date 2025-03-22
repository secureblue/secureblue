#!/usr/bin/bash
# Disable shellchecks for things that do not matter for
# a sourceable file
# shellcheck disable=SC2034,SC2155
########
### Text Formating
########
declare -r bold=$'\033[1m'
declare -r b="$bold"
declare -r dim=$'\033[2m'
declare -r underline=$'\033[4m'
declare -r u="$underline"
declare -r blink=$'\033[5m'
declare -r invert=$'\033[7m'
declare -r highlight="$invert"
declare -r hidden=$'\033[8m'

########
### Remove Text Formating
########
declare -r normal=$'\033[0m'
declare -r n="$normal"
declare -r unbold=$'\033[22m'
declare -r undim=$'\033[22m'
declare -r nounderline=$'\033[24m'
declare -r unblink=$'\033[25m'
declare -r uninvert=$'\033[27m'
declare -r unhide=$'\033[28m'

########
### Special text formating
########
## Function to generate a clickable link, you can call this using
# url=$(Urllink "https://ublue.it" "Visit the ublue website")
# echo "${url}"
function Urllink (){
    URL=$1
    TEXT=$2

    # Generate a clickable hyperlink
    printf "\033]8;;%s\033\\%s\033]8;;\033\\" "$URL" "$TEXT${n}"
}
