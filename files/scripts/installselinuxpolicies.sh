#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

dnf install -y --setopt=install_weak_deps=False policycoreutils-devel

policy_modules=(flatpakfull nautilus systemsettings thunar)

cil_policy_modules=(
    './selinux/user_namespace/grant_fm_userns.cil'
    './selinux/user_namespace/grant_userns.cil'
    './selinux/user_namespace/harden_userns.cil'
    './selinux/user_namespace/harden_container_userns.cil'
    './selinux/flatpakfull/grant_systemd_flatpak_exec.cil'
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
