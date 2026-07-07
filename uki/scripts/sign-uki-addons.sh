#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euxo pipefail

# Optional secureblue kernel arguments. Each one will be signed to make an
# individual UKI addon. Be careful with these! If they can make the system less
# secure when combined in a non-obvious way, we cannot revoke our signature.
addons=(
    "lockdown=confidentiality"
    "ia32_emulation=0"
    "nosmt=force"
    "amd_iommu=force_isolation"
    "bdev_allow_write_mounted=0"
    "debugfs=off"
    "efi=disable_early_pci_dma"
    "gather_data_sampling=force"
    "mem_encrypt=on"
    "oops=panic"
    "amdgpu.dcdebugmask=0x10" # https://invent.kde.org/kde-linux/kde-linux/-/merge_requests/431
)
# We need a UKI addon (karg or initrd) to get the right keyboard layout at the
# LUKS screen. Taken from `localectl list-keymaps`, deduplicated with niche ones
# removed.
keymaps=(
    ara be bg_bds-utf8 br-abnt2 ch ch-fr cz de dk ee es fa "fi" fr gb gr hr hu
    il it jp106 kr lt lv nl no pl pt ro rs-latin ru se si sk tr ua-utf us
)
addons+=("${keymaps[@]/#/vconsole.keymap=}")

mkdir /addons
for addon in "${addons[@]}"; do
    # The equals symbol is not allowed in FAT32 filenames, so replace it with __.
    filename="${addon//=/__}"
    ukify build \
        --cmdline "${addon}" \
        --signtool sbsign \
        --secureboot-private-key /run/secrets/secureboot_key \
        --secureboot-certificate /run/secrets/secureboot_crt \
        --output "/addons/${filename}.addon.efi"
done
