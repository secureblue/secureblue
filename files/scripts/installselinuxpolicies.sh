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

dnf install -y --setopt=install_weak_deps=False policycoreutils-devel make m4
dnf install -y --setopt=install_weak_deps=False fedora-repos-archive
selinux_policy_version_and_release=$(rpm -q --qf '%{VERSION}-%{RELEASE}' selinux-policy)
dnf install -y --setopt=install_weak_deps=False --repo=updates-archive "selinux-policy-devel-${selinux_policy_version_and_release}.noarch"

policy_modules=(trivalent flatpakfull nautilus systemsettings thunar)

cil_policy_modules=(
    './selinux/user_namespace/grant_fm_userns.cil'
    './selinux/user_namespace/grant_userns.cil'
    './selinux/user_namespace/harden_userns.cil'
    './selinux/user_namespace/harden_container_userns.cil'
    './selinux/flatpakfull/grant_systemd_flatpak_exec.cil'
    './selinux/user_namespace/userns_deny_unconfined_relabels.cil'
    './selinux/user_namespace/unbreak_thunar_thumbs.cil'
)

for module in "${policy_modules[@]}"; do
    cd "./selinux/${module}"
    make -f /usr/share/selinux/devel/Makefile "${module}.pp"
    cd ../..
done

semodule -v -i ./selinux/*/*.pp "${cil_policy_modules[@]}"

restorecon -FRv /usr

dnf remove -y fedora-repos-archive
