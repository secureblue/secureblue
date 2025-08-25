#!/usr/bin/bash
# Filename needs to be alphabetically later than vte.sh
if [ -n "${BASH_VERSION:-}" ]; then
    export PROMPT_COMMAND='__bash_prompt_command 2>/dev/null'

    __bash_prompt_command() {
        local prev_status="$?"
        if [ "$prev_status" != 0 ]; then
            # Print nonzero exit code in bold red text inside square brackets
            printf '\033[31m[\033[1m%s\033[22m]\033[39m' "$prev_status"
        fi
        # Default prompt taken from /etc/bashrc
        printf '\033]0;%s@%s:%s\007' "${USER}" "${HOSTNAME%%.*}" "${PWD/#$HOME/\~}"
    }
fi
