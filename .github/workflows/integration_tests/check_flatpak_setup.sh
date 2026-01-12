#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

service_name="secureblue-flatpak-setup.service"
timer_name="secureblue-flatpak-setup.timer"

test-fail() {
    echo "Test failed: $1"
    echo "Service status:"
    systemctl --user status --full "${service_name}" || true
    exit 1
}

check-flatpak-remotes() {
    if [ "$(flatpak remotes --columns=name)" != 'flathub-verified' ]; then
        test-fail "flathub-verified flatpak remote not present or not the only remote."
    fi
}

check-installed-flatpaks() {
    if [ "$(flatpak list --app --columns=application)" = 'com.github.tchx84.Flatseal' ]; then
        echo "Flatseal is installed."
    else
        test-fail "installed flatpaks were not as expected (Flatseal only)."
    fi
}

if ! systemctl --user is-enabled --quiet "${timer_name}"; then
    test-fail "${timer_name} is not enabled."
fi

# Wait a few seconds to give the service time to start
sleep 20

state=$(systemctl --user show "${service_name}" --property=ActiveState | sed 's/^ActiveState=//')

if [ -e "$HOME/.config/secureblue/secureblue-flatpak-setup.stamp" ]; then
    echo "${service_name} has successfully completed."
    check-flatpak-remotes
    check-installed-flatpaks
elif [ "${state}" = 'activating' ] || [ "${state}" = 'active' ]; then
    echo "${service_name} is currently running."
elif [ "${state}" = 'failed' ]; then
    test-fail "${service_name} is in a failed state."
else
    test-fail "${service_name} is enabled, but has not started for some reason."
fi
