#!/bin/bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -eou pipefail

[ "$UID" -eq 0 ] || { echo "This script must be run as root."; exit 1;}

backup_key_path="$(getent passwd "$SUDO_USER" | cut -d: -f6)"

if [ ! -d "$backup_key_path" ]; then
  # We assume the below path exists and is writeable for root.
  backup_key_path="/var/home"
fi

if [ ! "$(grep -c ^ "/etc/crypttab")" -eq 1 ]; then
  echo "Multi-drive setups not supported."
  exit 1
fi

echo "WARNING LUKS drive encryption must have been enabled at install time for this script to run" 
echo "ENSURE you save the backup key this script creates at $backup_key_path/luks_backup_key.txt ON ANOTHER COMPUTER"
echo ""
echo "This script uses systemd-cryptenroll to enable FIDO2 unlock. You can review systemd-cryptenroll's manpage for more information." \
"If you previously used TPM luks unlocking, ensure you run 'ujust remove-luks-tpm-unlock' AFTER running this script." \
"Otherwise, the system will likely default to TPM unlocking on boot."
echo ""
echo "If you are using usbguard, plug in your hardware key, run 'usbguard list-devices'. Identify which number on the left is" \
"your device then run 'usbguard allow-device <number> -p'. You must exit this script with ctrl-C and do this now, BEFORE proceeding"
echo ""
echo "WARNING this script is designed not to, but could clear stored secrets on your fido2 key. Ensure you have backup options for" \
"any sites you may use FIDO2 based authentication on this key."
echo ""
read -p "Are you sure are good with this and want to enable FIDO2 unlock? (y/N): " -n 1 -r
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
# Note: we use { grep "Keyslot" || true; } below to mask the nonzero return code if fido2 has not been setup yet
before_cryptenroll_keyslot=$(echo "$CRYPT_DISK_INFO" | sed -n '/systemd-fido2$/,/Keyslot:/p' | { grep "Keyslot" || true; } | awk '{print $2}')

if echo "$CRYPT_DISK_INFO" | grep systemd-fido2 > /dev/null; then
  echo "FIDO2 already present in LUKS keyslot $before_cryptenroll_keyslot of $CRYPT_DISK."
  read -p "Wipe it and re-enroll? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo
    echo "Either clear the existing FIDO2 keyslot before retrying, else choose 'y' next time."
    echo "Exiting..."
    [[ "$0" = "${BASH_SOURCE[0]}" ]] && exit 1 || return 1
  else
    systemd-cryptenroll --wipe-slot="fido2" "$CRYPT_DISK"
  fi
fi

## Run crypt enroll
echo "Enrolling FIDO2 unlock requires your existing LUKS unlock password"
systemd-cryptenroll --fido2-device=auto "$CRYPT_DISK"
cp /etc/crypttab /etc/crypttab.known-good
sed -i --sandbox "s/UUID=$(echo "$RD_LUKS_UUID" | cut -c6-) none discard/UUID=$(echo "$RD_LUKS_UUID" | cut -c6-) none - fido2-device=auto - discard/" /etc/crypttab

CRYPT_DISK_INFO=$(cryptsetup luksDump "$CRYPT_DISK")
# Sets the new fido2 keyslot as preferred if it's the only one currently configured. (Users with more than one configured are presumed advanced and capable of their own priority management.)
if [ "$(echo "$CRYPT_DISK_INFO" | grep -c "systemd-fido2")" -eq "1" ]; then
  after_cryptenroll_keyslot=$(echo "$CRYPT_DISK_INFO" | sed -n '/systemd-fido2$/,/Keyslot:/p' | { grep "Keyslot" || true; } | awk '{print $2}')
  cryptsetup config --key-slot "$after_cryptenroll_keyslot" --priority "prefer" "$CRYPT_DISK"
fi

echo "Creating backup key"
systemd-cryptenroll --recovery-key "$CRYPT_DISK" > "$backup_key_path/luks_backup_key.txt"
chmod 640 "$backup_key_path/luks_backup_key.txt"
chown "$SUDO_USER":"$SUDO_USER" "$backup_key_path/luks_backup_key.txt"

if lsinitrd 2>&1 | grep -q fido2 > /dev/null; then
  ## add fido2 to initramfs
  if rpm-ostree initramfs | grep fido2 > /dev/null; then
    echo "FIDO2 already present in rpm-ostree initramfs config."
    rpm-ostree initramfs
    echo "Re-running initramfs to pickup changes above."
  fi
  rpm-ostree initramfs --enable --arg=--force-add --arg=fido2
else
  ## initramfs already contains fido2
  echo "FIDO2 already present in initramfs."
fi

echo "Congratulations!"
echo "Your system is now configured to use FIDO2 unlocking via the hardware key you used earlier. If you previously used TPM luks unlocking, ensure you run 'ujust remove-luks-tpm-unlock'. Otherwise, the system will continue to accept the comparatively insecure tpm credentials."
echo ""
echo "REMINDER: Store on another computer, on an encrypted drive, the script created backup key (which is at $backup_key_path/luks_backup_key.txt)"

# References
# https://0pointer.net/blog/unlocking-luks2-volumes-with-tpm2-fido2-pkcs11-security-hardware-on-systemd-248.html
# https://www.freedesktop.org/software/systemd/man/latest/crypttab.html
