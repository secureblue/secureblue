#!/usr/bin/env bash

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

service_name="secureblue-flatpak-setup.service"
timer_name="secureblue-flatpak-setup.timer"

test-fail() {
    echo "Test failed: $1"
    echo "Service status:"
    systemctl --user status --full "${service_name}" || true
    exit 1
}

if ! systemctl --user is-enabled --quiet "${timer_name}"; then
    test-fail "${timer_name} is not enabled."
fi

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

state=$(systemctl --user show "${service_name}" --property=ActiveState | sed 's/^ActiveState=//')

if [ -e "$HOME/.config/secureblue/secureblue-flatpak-setup.stamp" ]; then
    echo "${service_name} has successfully completed."
    check-flatpak-remotes
    check-installed-flatpaks
elif [ "${state}" = 'activating' ] || [ "${state}" = 'active' ]; then
    echo "${service_name} is currently running."
    # flathub-verified should be added right at the start of the service, so we test for it.
    check-flatpak-remotes
elif [ "${state}" = 'failed' ]; then
    test-fail "${service_name} is in a failed state."
else
    test-fail "${service_name} is enabled, but has not started for some reason."
fi
