# shellcheck shell=bash
# Filename needs to be alphabetically later than vte.sh

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Print nonzero exit codes in bold red text inside square brackets at beginning of prompt
case "$-" in
*i*)
    # We use the POSIX test here so this doesn't give a syntax error if sourced
    # by a non-bash shell.
    # shellcheck disable=SC2292
    if [ -n "${BASH_VERSION-}" ]; then
        __scbl_ps1_exit_code() {
            # Only print the function name during xtrace for cleaner output
            {
                local -
                set +x
            } 2>/dev/null

            if [[ "$1" == 0 ]]; then
                return
            fi

            # https://www.gnu.org/software/bash/manual/html_node/Controlling-the-Prompt.html
            local -r ps1_prefix=(
                '\[\e[31m\]' # red
                "["
                '\[\e[1m\]' # bold
                "$1"
                '\[\e[22m\]' # default intensity
                "]"
                '\[\e[39m\]' # default color
            )

            # @P tells Bash to expand the values as a prompt string
            printf '%s' "${ps1_prefix[@]@P}"
        }

        # shellcheck disable=SC2154
        PS1='$(__scbl_ps1_exit_code "$?")'"${PS1:-}"
    fi
    ;;
esac
