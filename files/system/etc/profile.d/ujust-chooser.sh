#!/usr/bin/sh

if command -v fzf > /dev/null 2>&1
then
    unset JUST_CHOOSER
else
    export JUST_CHOOSER=/usr/bin/echo
fi
