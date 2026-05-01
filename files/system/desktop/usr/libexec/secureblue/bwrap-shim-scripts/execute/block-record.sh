#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 Commenter25
#
# SPDX-License-Identifier: Apache-2.0

declare name debug should_execute

execute() {
	declare -r config_path=${should_execute["block-record"]}
	[[ "${config_path}" != "" ]] || return

	subname="${name}: BLOCK-RECORD"

	local -r jq_filter='
	if .block_by_default then
		if (.allowed | index("'"${flatpak_name}"'") != null)
		then "allow" else "block" end
	else
		if (.blocked | index("'"${flatpak_name}"'") != null)
		then "block" else "allow" end
	end
	'

	local -l permission="block"
	if [[ -n ${flatpak_name} ]]; then
		permission=$(jq --raw-output "${jq_filter}" "${config_path}")
	fi
	local -r permission

	# we know the user has a config, so we want to block by default for their safety
	if [[ "${permission}" != "allow" ]]; then
		extra_bwrap_args+=( "--tmpfs" "/dev/snd" )
	fi

	[[ "${debug}" = true ]] && echo "${subname}: Value returned was ${permission}"

}
execute
unset -f execute
