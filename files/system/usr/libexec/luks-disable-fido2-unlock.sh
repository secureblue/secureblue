#!/bin/bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -eou pipefail

[ "$UID" -eq 0 ] || { echo "This script must be run as root."; exit 1;}

echo "WARNING this script will remove ALL currently configured fido2 luks unlock slots."
echo ""
echo "This script utilizes systemd-cryptenroll for removing fido2 unlock. You can review systemd-cryptenroll's manpage for more information." \
"This will modify your system and disable fido2 unlock of your LUKS partition! This script is designed to work with it's corresponding secureblue" \
"fido2 enable script. If you manually enabled fido2 unlock, you may need to manually edit /etc/crypttab or restore a known good backup you may have created." 
echo ""
echo "INFO if no other nonfido2 slot is currently configured, script will fail. This is a safety precaution systemd-cryptenroll implements."
echo "WARNING if you have not added an additional method, the recovery key will be the only avaliable unlock method after this script is run"
read -p "Are you sure are good with this and want to disable fido2 unlock? (y/N): " -n 1 -r
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

## Restore the crypttab
cp -a /etc/crypttab /etc/crypttab.working-before-disable-fido2
if [ -f /etc/crypttab.known-good ]; then
  echo "Restoring /etc/crypttab.known-good to original /etc/crypttab"
  mv /etc/crypttab.known-good /etc/crypttab
fi

## Wipe luks slot
if cryptsetup luksDump "$CRYPT_DISK" | grep systemd-fido2 > /dev/null; then
  echo "Wiping systemd-fido2 from LUKS on $CRYPT_DISK"
  systemd-cryptenroll --wipe-slot=fido2 "$CRYPT_DISK"
else
  echo "No systemd-fido2 found in LUKS to wipe"
fi

echo "FIDO2 unlock disabled..."
