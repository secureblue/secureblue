#!/usr/bin/bash
# Filename needs to be alphabetically later than vte.sh

# Print nonzero exit codes in bold red text inside square brackets at beginning of prompt
if [[ $- == *i* && -n "${BASH_VERSION:-}" ]]; then
    __scbl_ps1_exit_code() {
        # Only print the function name during xtrace for cleaner output
        { local -; set +x; } 2>/dev/null

        local start
        start+=$'\e[31m' # red
        start+="["
        start+=$'\e[1m' # bold

        local end
        end+=$'\e[22m' # default intensity
        end+="]"
        end+=$'\e[39m' # default color

        local -r code=${1#0}
        echo -n "${code:+${start}${code}${end}}"
    }

    # shellcheck disable=SC2154
    PS1='$(__scbl_ps1_exit_code $?)'"${PS1:-}"
fi
