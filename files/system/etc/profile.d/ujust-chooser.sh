#!/usr/bin/env bash

if command -v fzf &> /dev/null
then
    export JUST_CHOOSER="fzf --multi --preview 'just --unstable --color always --justfile \"/usr/share/ublue-os/justfile\" --show {}'"
else
    export JUST_CHOOSER=/usr/bin/echo
fi
