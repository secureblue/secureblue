#!/bin/bash

# Copyright 2025 Universal Blue
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

set -eou pipefail

[ "$UID" -eq 0 ] || { echo "This script must be run as root."; exit 1;}

echo "WARNING this script will remove ALL currently configured fido2 luks unlock slots."
echo ""
echo "This script utilizes systemd-cryptenroll for removing fido2 auto-unlock. You can review systemd-cryptenroll's manpage for more information." \
"This will modify your system and disable fido2 auto-unlock of your LUKS partition! This script is designed to work with it's corresponding secureblue" \
"fido2 enable script. If you manually enabled fido2 unlock, you may need to manually edit /etc/crypttab or restore a known good backup you may have created." 
echo ""
echo "INFO if no other nonfido2 slot is currently configured, script will fail. This is a safety precaution systemd-cryptenroll implements."
echo "WARNING if you have not added an additional method, the recovery key will be the only avaliable unlock method after this script is run"
read -p "Are you sure are good with this and want to disable fido2 auto-unlock? (y/N): " -n 1 -r
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

echo "FIDO2 auto-unlock disabled..."
