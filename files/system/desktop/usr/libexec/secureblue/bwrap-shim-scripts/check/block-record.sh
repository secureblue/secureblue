#!/usr/bin/env bash
# shellcheck disable=SC2154 # all external variables

# SPDX-FileCopyrightText: Copyright 2026 Commenter25
#
# SPDX-License-Identifier: Apache-2.0

check() {
	local -r config="${user_config}/secureblue/ujust-block-record.json"
	if [[ -e "${config}" ]]; then
		should_execute+=( ["block-record"]="${config}" )
	else
		should_execute+=( ["block-record"]="" )
		(( check_fail_count += 1 ))
	fi
}
check
unset -f check
