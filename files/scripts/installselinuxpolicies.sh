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

semodule -v -i ./selinux/*/*.pp "${cil_policy_modules[@]}"

restorecon -FRv /usr
