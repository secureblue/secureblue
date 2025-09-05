#!/usr/bin/env bash

if command -v fzf &> /dev/null
then
    export JUST_CHOOSER="fzf"
else
    export JUST_CHOOSER=/usr/bin/echo
fi
