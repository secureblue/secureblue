#!/usr/bin/bash
# Filename needs to be alphabetically later than vte.sh

# Print nonzero exit codes in bold red text inside square brackets at beginning of prompt
if [[ $- == *i* && -n "${BASH_VERSION:-}" ]]; then
    __scbl_ps1_exit_code() {
        # Only print the function name during xtrace for cleaner output
        { local -; set +x; } 2>/dev/null

        if [[ "$1" == 0 ]]; then
            return
        fi

        local -r ps1_prefix=(
            $'\e[31m' # red
            "["
            $'\e[1m' # bold
            "$1"
            $'\e[22m' # default intensity
            "]"
            $'\e[39m' # default color
        )

        printf '%s' "${ps1_prefix[@]}"
    }

    # shellcheck disable=SC2154
    PS1='$(__scbl_ps1_exit_code "$?")'"${PS1:-}"
fi
