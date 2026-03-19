#!/bin/bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

## setup unlock LUKS2 encrypted root on Fedora/Silverblue/maybe others
set -eou pipefail


[ "$UID" -eq 0 ] || { echo "This script must be run as root."; exit 1;}

echo "WARNING: Do NOT use this if your CPU is vulnerable to faulTPM!"
echo "All AMD Zen2 and Zen3 Processors are known to be affected!"
echo "All AMD Zen1 processors are also likely affected, with Zen4 unknown!"
echo "If you have an AMD CPU, you likely shouldn't use this!"
echo "----------------------------------------------------------------------------"
echo "This script uses systemd-cryptenroll to enable TPM2 unlock."
echo "You can review systemd-cryptenroll's manpage for more information."
echo "This script will modify your system."
echo "It will enable TPM2 unlock of your LUKS partition for your root device!"
echo "It will bind to PCR 7 and 14 which is tied to your secureboot and moklist state."
read -p "Are you sure are good with this and want to enable TPM2 unlock? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  [[ "$0" = "${BASH_SOURCE[0]}" ]] && exit 1 || return 1 # handle exits from shell or function but don't exit interactive shell
fi

## Inspect Kernel Cmdline for rd.luks.uuid
RD_LUKS_UUID="$(xargs -n1 -a /proc/cmdline | grep rd.luks.uuid | cut -d = -f 2)"

# Check to make sure cmdline rd.luks.uuid exists
if [[ -z ${RD_LUKS_UUID:-} ]]; then
  printf "LUKS device not defined on Kernel Commandline.\n"
  printf "This is not supported by this script.\n"
  printf "Exiting...\n"
  exit 1
fi

# Check to make sure that the specified cmdline uuid exists.
if ! grep -q "${RD_LUKS_UUID}" <<< "$(lsblk)" ; then
  printf "LUKS device not listed in block devices.\n"
  printf "Exiting...\n"
  exit 1
fi

# Cut off the luks-
LUKS_PREFIX="luks-"
if grep -q ^${LUKS_PREFIX} <<< "${RD_LUKS_UUID}"; then
  DISK_UUID=${RD_LUKS_UUID#"$LUKS_PREFIX"}
else
  echo "LUKS UUID format mismatch."
  echo "Exiting..."
  exit 1
fi

# Specify Crypt Disk by-uuid
CRYPT_DISK="/dev/disk/by-uuid/$DISK_UUID"

# Check to make sure crypt disk exists
if [[ ! -L "$CRYPT_DISK" ]]; then
  printf "LUKS device not listed in block devices.\n"
  printf "Exiting...\n"
  exit 1
fi

CRYPT_DISK_INFO=$(cryptsetup luksDump "$CRYPT_DISK")
existing_KEYSLOT=$(echo "$CRYPT_DISK_INFO" | sed -n '/systemd-tpm2$/,/Keyslot:/p' | { grep "Keyslot" || true; } | awk '{print $2}') 

if echo "$CRYPT_DISK_INFO" | grep systemd-tpm2 > /dev/null; then
  echo "TPM2 already present in LUKS keyslot $existing_KEYSLOT of $CRYPT_DISK."
  read -p "Wipe it and re-enroll? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemd-cryptenroll --wipe-slot=tpm2 "$CRYPT_DISK"
  else
    echo
    echo "Either clear the existing TPM2 keyslot before retrying, else choose 'y' next time."
    echo "Exiting..."
    [[ "$0" = "${BASH_SOURCE[0]}" ]] && exit 1 || return 1
  fi
fi

## Run crypt enroll
echo "Enrolling TPM2 unlock requires your existing LUKS2 unlock password"
systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7+14 --tpm2-with-pin=yes "$CRYPT_DISK"

# Sets the new tpm keyslot as preferred if it's the only one currently configured. (Users with more than one configured are presumed advanced and capable of their own priority management. Not certain how or why you'd have more than one tpm2 keyslot regardless.)
if [ "$(echo "$CRYPT_DISK_INFO" | grep -c "systemd-tpm2")" -eq "1" ]; then
  new_KEYSLOT=$(echo "$CRYPT_DISK_INFO" | sed -n '/systemd-tpm2$/,/Keyslot:/p' | { grep "Keyslot" || true; } | awk '{print $2}')
  cryptsetup config --key-slot "$new_KEYSLOT" --priority "prefer" "$CRYPT_DISK"
fi

if lsinitrd 2>&1 | grep -q tpm2-tss > /dev/null; then
  ## add tpm2-tss to initramfs
  if rpm-ostree initramfs | grep tpm2 > /dev/null; then
    echo "TPM2 already present in rpm-ostree initramfs config."
    rpm-ostree initramfs
    echo "Re-running initramfs to pickup changes above."
  fi
  rpm-ostree initramfs --enable --arg=--force-add --arg=tpm2-tss
else
  ## initramfs already containts tpm2-tss
  echo "TPM2 already present in initramfs."
fi

echo
echo "TPM2 LUKS unlock configured."


# References:
#  https://www.reddit.com/r/Fedora/comments/uo4ufq/any_way_to_get_systemdcryptenroll_working_on/
#  https://0pointer.net/blog/unlocking-luks2-volumes-with-tpm2-fido2-pkcs11-security-hardware-on-systemd-248.html
