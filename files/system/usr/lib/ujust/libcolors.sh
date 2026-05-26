#!/usr/bin/bash
# Disable shellchecks for things that do not matter for
# a sourceable file
# shellcheck disable=SC2034,SC2155
########
### Basic Colors
### the bg function allows flipping these to background colors
### using the 90-97 colors is not supported by the bg function
### add them as extended colors instead which uses
### option 38 (foreground) which can be flipped to 48 (background)
########
declare -r black=$'\033[30m'
declare -r red=$'\033[31m'
declare -r green=$'\033[32m'
declare -r yellow=$'\033[33m'
declare -r blue=$'\033[34m'
declare -r magenta=$'\033[35m'
declare -r purple="$magenta"
declare -r cyan=$'\033[36m'
declare -r lightgrey=$'\033[37m'
declare -r lightgray="$lightgrey"

########
### Extended Colors
### You can use cpick from https://github.com/ethanbaker/cpick to get the colors
### cpick bash varname | sed -E 's/readonly/declare/'
########
declare -r darkgrey=$'\033[38;2;168;168;168m'
declare -r darkgray="$darkgrey"
declare -r lightred=$'\033[38;2;255;114;118m'
declare -r lightgreen=$'\033[38;2;146;240;146m'
declare -r lightyellow=$'\033[38;2;255;255;224m'
declare -r lightblue=$'\033[38;2;172;215;230m'
declare -r pink=$'\033[38;2;255;20;146m'
declare -r lightmagenta="$pink"
declare -r lightcyan=$'\033[38;2;224;255;255m'
declare -r white=$'\033[38;2;250;235;215m'
declare -r lightpink=$'\033[38;2;255;181;192m'
declare -r darkorange=$'\033[38;2;255;129;3m'

## Function to generate background color from foreground color
## NOTE: doublequote the color or future calls to bg will error out!
# bgblue=$(Bg "$blue")
# echo "${bgblue}text now has blue background${normal} this text has no background color"
function Bg (){
    COLOR="$1"
    
    # Flip foreground to background
    echo "$COLOR" | sed -E 's/\[3([0-8]{1,1})/\[4\1/'
}
