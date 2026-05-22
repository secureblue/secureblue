#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 Commenter25
#
# SPDX-License-Identifier: Apache-2.0

declare name debug should_execute flatpak_name

execute() {
	declare -r config_path=${should_execute["block-record"]:-}
	[[ "${config_path}" != "" ]] || return

	# shellcheck disable=SC2016 # jq varaibles
	local -r jq_filter='
	if .block_by_default then
		.allowed | index("$flatpak")
	else
		.blocked | index("$flatpak") | not
	end
	'

	# if jq fails for any reason, block by default to be safe; only succeeds if app is known allowed
	if ! jq --exit-status --arg flatpak "${flatpak_name}" -- "${jq_filter}" "${config_path}" &> /dev/null; then
		extra_bwrap_args+=( "--tmpfs" "/dev/snd" )
		if [[ "${debug}" = true ]]; then
			echo "${name}: BLOCK-RECORD: Blocking ALSA access"
		fi
	fi
}
execute
unset -f execute
