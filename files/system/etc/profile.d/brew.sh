#!/usr/bin/env bash
if [[ -d /home/linuxbrew/.linuxbrew && $- == *i* && "$(/usr/bin/id -u)" != 0 ]]; then
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
fi
