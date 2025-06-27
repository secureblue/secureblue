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

rpm-ostree install selinux-policy-devel

cd ./selinux/trivalent
bash trivalent.sh
cd ../..

cd ./selinux/flatpakfull
bash flatpakfull.sh
cd ../..

cd ./selinux/nautilus
bash nautilus.sh
cd ../..

cd ./selinux/systemsettings
bash systemsettings.sh
cd ../..

semodule -i ./selinux/user_namespace/grant_userns.cil
semodule -i ./selinux/user_namespace/harden_userns.cil
semodule -i ./selinux/user_namespace/harden_container_userns.cil
semodule -i ./selinux/flatpakfull/grant_systemd_flatpak_exec.cil

semodule -i ./selinux/user_namespace/deny_unconfined_blk_file_relabels.cil
semodule -i ./selinux/user_namespace/deny_unconfined_chr_file_relabels.cil
semodule -i ./selinux/user_namespace/deny_unconfined_dir_relabels.cil
semodule -i ./selinux/user_namespace/deny_unconfined_fifo_file_relabels.cil
semodule -i ./selinux/user_namespace/deny_unconfined_file_relabels.cil
semodule -i ./selinux/user_namespace/deny_unconfined_lnk_file_relabels.cil