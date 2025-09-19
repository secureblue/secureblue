#!/usr/bin/env bash

if command -v fzf &> /dev/null
then
    unset JUST_CHOOSER
else
    export JUST_CHOOSER=/usr/bin/echo
fi
