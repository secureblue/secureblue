#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

flatpak_service_name="secureblue-flatpak-setup.service"
flatpak_timer_name="secureblue-flatpak-setup.timer"
bazaar_service_name="secureblue-bazaar-setup.service"
bazaar_timer_name="secureblue-bazaar-setup.timer"

test-fail() {
    echo "Test failed: $1"
    echo "Service status:"
    systemctl --user status --full "${flatpak_service_name}" || true
    systemctl --user status --full "${bazaar_service_name}" || true
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

for timer in "${flatpak_timer_name}" "${bazaar_timer_name}"; do
    if ! systemctl --user is-enabled --quiet "${timer}"; then
        test-fail "${flatpak_timer_name} is not enabled."
    fi
done

# Wait a few seconds to give the services time to start
sleep 20


for service_name in "${flatpak_service_name}" "${bazaar_timer_name}"; do
    state=$(systemctl --user show "${service_name}" --property=ActiveState | sed 's/^ActiveState=//')

    config_dir=${XDG_CONFIG_HOME:-"${HOME}/.config"}
    if [[ -e "${config_dir}/secureblue/secureblue-flatpak-setup.stamp" ]]; then
        echo "${service_name} has successfully completed."
        check-flatpak-remotes
        check-installed-flatpaks
    elif [[ "${state}" = 'activating' ]] || [[ "${state}" = 'active' ]]; then
        echo "${service_name} is currently running."
    elif [[ "${state}" = 'failed' ]]; then
        test-fail "${service_name} is in a failed state."
    else
        test-fail "${service_name} is enabled, but has not started for some reason."
    fi
done
