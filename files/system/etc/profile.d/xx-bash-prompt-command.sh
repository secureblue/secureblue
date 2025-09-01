#!/usr/bin/bash
# Filename needs to be alphabetically later than vte.sh
if [[ $- == *i* && -n "${BASH_VERSION:-}" ]]; then
    # Print nonzero exit codes in bold red text inside square brackets at beginning of prompt
    export PS1='$(code=${?#0};echo -n "${code:+\[\e[31m\][\[\e[1m\]${code}\[\e[22m\]]\[\e[39m\]}")'"${PS1:-}"
fi
