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

resolv_conf="/etc/resolv.conf"
dnsconfd_service="dnsconfd.service"
unbound_service="unbound.service"
dnsconfd_exec_path="/usr/bin/dnsconfd"
dnsconfd_exec_expected="system_u:object_r:dnsconfd_exec_t:s0 ${dnsconfd_exec_path}"

test_fail() {
    echo "Test failed: $1"
    echo "Service statuses:"
    systemctl status "$dnsconfd_service" --full || true
    systemctl status "$unbound_service" --full || true
    exit 1
}

if [ ! -f "$resolv_conf" ]; then
    test_fail "resolv.conf is missing."
fi
echo "resolv.conf is present."

if [ -L "$resolv_conf" ]; then
    test_fail "resolv.conf is still a symlink, presumably a systemd-resolved stub."
fi
echo "resolv.conf is not a symlink."

if ! systemctl is-enabled --quiet "$dnsconfd_service"; then
    test_fail "$dnsconfd_service is not enabled."
fi
echo "$dnsconfd_service is enabled."

if ! systemctl is-active --quiet "$dnsconfd_service"; then
    test_fail "$dnsconfd_service is not running."
fi
echo "$dnsconfd_service is running."

if ! systemctl is-active --quiet "$unbound_service"; then
    test_fail "$unbound_service is not running."
fi
echo "$unbound_service is running."

# dnsconfd.fc <=v1.7.2 is broken, ensure any workaround is working.
dnsconfd_exec_info=$(ls -Z "$dnsconfd_exec_path")
if [ "$dnsconfd_exec_info" != "$dnsconfd_exec_expected" ]; then
    test_fail "$dnsconfd_exec_path is not dnsconfd_exec_t."
fi
echo "$dnsconfd_exec_path has the expected SELinux type."
