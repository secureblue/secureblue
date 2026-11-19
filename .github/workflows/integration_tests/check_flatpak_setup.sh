#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

services_to_check=("bazaar" "flatpak")

test-fail() {
    echo "Test failed: $1"
    echo "Service status:"
    for service in "${services_to_check[@]}"; do
        systemctl --user status --full "secureblue-${service}-setup.service" || true
    done
    exit 1
}

check-flatpak-remotes() {
    if [[ "$(flatpak remotes --columns=name)" != 'flathub' ]]; then
        test-fail "Flathub Flatpak remote not present or not the only remote."
    fi
    if [[ "$(flatpak remotes --columns=subset)" != 'verified' ]]; then
        test-fail "Flathub Flatpak remote is not restricted to the verified subset."
    fi
}

check-installed-flatpaks() {
    installed_flatpaks=$(flatpak list --app --columns=application)
    installed_flatpaks_count=$(echo "${installed_flatpaks}" | wc -l)
    if [[ "${installed_flatpaks}" = *'com.github.tchx84.Flatseal'*
        && "${installed_flatpaks}" = *'io.github.kolunmi.Bazaar'*
        && "${installed_flatpaks_count}" = '2' ]]; then
        echo "Flatseal and Bazaar are installed."
    else
        test-fail "Installed Flatpaks were not as expected (Flatseal and Bazaar only)."
    fi
}

for unit in secureblue-bazaar-setup.timer secureblue-flatpak-setup.timer; do
    if ! systemctl --user is-enabled --quiet "${unit}"; then
        test-fail "${unit} is not enabled."
    fi
done

# Wait a few seconds to give the services time to start
sleep 20


for service in "${services_to_check[@]}"; do
    systemd_service_name="secureblue-${service}-setup.service"
    state=$(systemctl --user show "${systemd_service_name}" --property=ActiveState | sed 's/^ActiveState=//')
    job=$(systemctl --user show "${systemd_service_name}" --property=Job | sed 's/^Job=//')
    config_dir=${XDG_CONFIG_HOME:-"${HOME}/.config"}
    if [[ "${service}" = 'bazaar' ]]; then
        config_dir=${XDG_STATE_HOME:-"${HOME}/.local/state"}
    fi
    stamp_file="${config_dir}/secureblue/secureblue-${service}-setup.stamp"
    if [[ -e "${stamp_file}" ]]; then
        echo "${systemd_service_name} has successfully completed."
        if [[ "${service}" = 'flatpak' ]]; then
            check-flatpak-remotes
        fi

        if [[ "${service}" = 'bazaar' ]]; then
            check-installed-flatpaks
        fi
    elif [[ "${state}" = 'activating' ]] || [[ "${state}" = 'active' ]] || [[ -n "${job}" ]]; then
        echo "${systemd_service_name} is currently running."
    elif [[ "${state}" = 'failed' ]]; then
        test-fail "${systemd_service_name} is in a failed state."
    else
        test-fail "${systemd_service_name} is enabled, but has not started for some reason."
    fi
done
