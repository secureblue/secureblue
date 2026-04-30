#!/usr/bin/env bash
# shellcheck disable=SC2034 # vars for use by sourced scripts

# SPDX-FileCopyrightText: Copyright 2026 Commenter25
#
# SPDX-License-Identifier: Apache-2.0

user_id=$(id -u)
declare -r user_id

if [[ -v HOME ]]; then
	user_home="${HOME}"
else
	user_home="$(getent passwd "${user_id}")"
	user_home="${user_home%:*}" # remove last field
	user_home="${user_home##*:}" # remove all but last field
fi
declare -r user_home

declare -r user_config="${XDG_CONFIG_HOME:-"${user_home}/.config"}"

declare -A should_execute=()
