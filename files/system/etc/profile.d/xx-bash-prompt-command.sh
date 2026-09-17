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

        # https://www.gnu.org/software/bash/manual/html_node/Controlling-the-Prompt.html
        local -r esc='\[\e[!m\]'

        local -r ps1_prefix=(
            "${esc/!/31}" # red
            "["
            "${esc/!/1}" # bold
            "$1"
            "${esc/!/22}" # default intensity
            "]"
            "${esc/!/39}" # default color
        )

        # @P tells Bash to expand the values as a prompt string
        printf '%s' "${ps1_prefix[@]@P}"
    }

    # shellcheck disable=SC2154
    PS1='$(__scbl_ps1_exit_code "$?")'"${PS1:-}"
fi
