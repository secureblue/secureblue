#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

selinux_policy_version="$(rpm -q --qf '%{version}-%{release}' selinux-policy)"
dnf install -y --setopt=install_weak_deps=False --enable-repo=updates-archive \
    "selinux-policy-devel-${selinux_policy_version}"

policy_modules=(flatpakfull nautilus systemsettings thunar)

cil_policy_modules=(
    './selinux/flatpakfull/grant_systemd_flatpak_exec.cil'
    './selinux/ptrace/container-ptrace.cil'
    './selinux/sockets/secureblue_audit_sockets.cil'
    './selinux/sockets/secureblue_deny_alg_sockets.cil'
    './selinux/sockets/secureblue_deny_ipsec_sockets.cil'
    './selinux/sockets/secureblue_deny_obscure_sockets.cil'
    './selinux/sockets/secureblue_deny_packet_radio_sockets.cil'
    './selinux/sockets/secureblue_socket_utils.cil'
    './selinux/user_namespace/grant_fm_userns.cil'
    './selinux/user_namespace/grant_userns.cil'
    './selinux/user_namespace/harden_container_userns.cil'
    './selinux/user_namespace/harden_userns.cil'
    './selinux/user_namespace/userns_deny_unconfined_relabels.cil'
)

for module in "${policy_modules[@]}"; do
    cd "./selinux/${module}"
    make -f /usr/share/selinux/devel/Makefile "${module}.pp"
    cd ../..
done

# Install at priority 300 to be higher-priority than policies from RPM packages
# (which are conventionally priority 200) but lower-priority than custom
# policies set by a local administrator (which default to priority 400).
semodule -v -X 300 -i ./selinux/*/*.pp "${cil_policy_modules[@]}"

restorecon -FRv /usr
