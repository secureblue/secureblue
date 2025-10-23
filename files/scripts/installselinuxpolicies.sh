#!/usr/bin/env bash

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

set -oue pipefail

dnf install -y --setopt=install_weak_deps=False selinux-policy-devel

policy_modules=(trivalent flatpakfull nautilus systemsettings thunar)

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
