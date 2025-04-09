#!/usr/bin/env bash

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