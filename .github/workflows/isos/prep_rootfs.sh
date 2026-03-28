#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2024 Universal Blue
# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail


IMAGE_TAG="br-next-44"
IMAGE_VARIANT_ID=$(grep '^VARIANT_ID=' /etc/os-release | cut -d= -f2)
IMAGE_REF="ostree-image-signed:docker://ghcr.io/secureblue/$IMAGE_VARIANT_ID"
IMAGE_REF="${IMAGE_REF##*://}"

sed -i '/^install squashfs \/bin\/false$/d' /usr/lib/modprobe.d/secureblue.conf

systemctl disable bootloader-update.service
systemctl disable rpm-ostree-countme.service

dnf remove -y google-noto-fonts-all homebrew
dnf install -y secureblue-logos
dnf reinstall -y polkit
dnf install -y anaconda-live libblockdev-btrfs libblockdev-btrfs libblockdev-lvm libblockdev-dm

systemctl disable --global secureblue-flatpak-setup.service
systemctl disable --global secureblue-flatpak-setup.timer
systemctl disable --global podman-auto-update.timer
systemctl disable --global flatpak-user-update.timer
systemctl disable rpm-ostreed-automatic.timer
systemctl disable rpm-ostree-countme.service

rm -f /usr/share/applications/org.mozilla.Firefox.desktop
rm -f /usr/share/applications/org.mozilla.firefox.desktop
rm -f /usr/share/applications/firefox.desktop
rm -f /usr/share/applications/firefox-wayland.desktop
rm -f /usr/share/applications/firefox-x11.desktop

# add intaller to kickoff
sed -i '2s/$/;liveinst.desktop/' /usr/share/kde-settings/kde-profile/default/xdg/kicker-extra-favoritesrc || true

jq '.transports["containers-storage"][""][0].type = "insecureAcceptAnything"' /etc/containers/policy.json | tee /etc/containers/policy.json.tmp && mv /etc/containers/policy.json.tmp /etc/containers/policy.json

# Disable suspend/sleep during live environment and initial setup
# This prevents the system from suspending during installation or first-boot user creation
tee /usr/share/glib-2.0/schemas/zz3-secureblue-installer-power.gschema.override <<EOF
[org.gnome.settings-daemon.plugins.power]
sleep-inactive-ac-type='nothing'
sleep-inactive-battery-type='nothing'
sleep-inactive-ac-timeout=0
sleep-inactive-battery-timeout=0

[org.gnome.desktop.session]
idle-delay=uint32 0
EOF


# don't autostart gnome-software session service
rm -f /etc/xdg/autostart/org.gnome.Software.desktop

# disable the gnome-software shell search provider
tee /usr/share/gnome-shell/search-providers/org.gnome.Software-search-provider.ini <<EOF
DefaultDisabled=true
EOF


sed -i 's| Fedora| secureblue|' /usr/share/anaconda/gnome/fedora-welcome || true
sed -i -e "s/Fedora/secureblue/g" /usr/share/anaconda/gnome/org.fedoraproject.welcome-screen.desktop

tee /etc/anaconda/profile.d/secureblue.conf <<'EOF'
# Anaconda configuration file for secureblue

[Profile]
# Define the profile.
profile_id = secureblue

[Profile Detection]
# Match os-release values
os_id = secureblue

[Network]
default_on_boot = FIRST_WIRED_WITH_LINK

[Bootloader]
efi_dir = fedora
menu_auto_hide = True

[Storage]
default_scheme = BTRFS
btrfs_compression = zstd:1
default_partitioning =
    /     (min 1 GiB, max 70 GiB)
    /home (min 500 MiB, free 50 GiB)
    /var  (btrfs)

[User Interface]
webui_web_engine = /usr/local/bin/trivalent-webui
custom_stylesheet = /usr/share/anaconda/pixmaps/silverblue/fedora-silverblue.css
hidden_spokes =
    NetworkSpoke
    PasswordSpoke
hidden_webui_pages =
    root-password
    network
password_policies = 
        root (quality 100, length 15)
        user (quality 50, length 15)
        luks (quality 100, length 20)
EOF


# Fetch the Secureboot Public Key
sbkey='https://github.com/secureblue/secureblue/raw/refs/heads/live/files/system/etc/pki/akmods/certs/akmods-secureblue.der'
curl --retry 15 -Lo /etc/sb_pubkey.der "$sbkey"

# Enroll Secureboot Key
tee /usr/share/anaconda/post-scripts/secureboot-enroll-key.ks <<'EOF'
%post --erroronfail --nochroot
set -oue pipefail

readonly ENROLLMENT_PASSWORD="secureblue"
readonly SECUREBOOT_KEY="/etc/sb_pubkey.der"

if [[ ! -d "/sys/firmware/efi" ]]; then
    echo "EFI mode not detected. Skipping key enrollment."
    exit 0
fi

if [[ ! -f "$SECUREBOOT_KEY" ]]; then
    echo "Secure boot key not provided: $SECUREBOOT_KEY"
    exit 0
fi

SYS_ID="$(cat /sys/devices/virtual/dmi/id/product_name)"
if [[ ":Jupiter:Galileo:" =~ ":$SYS_ID:" ]]; then
    echo "Steam Deck hardware detected. Skipping key enrollment."
    exit 0
fi

mokutil --timeout -1 || :
echo -e "$ENROLLMENT_PASSWORD\n$ENROLLMENT_PASSWORD" | mokutil --import "$SECUREBOOT_KEY" || :
%end
EOF


# Interactive Kickstart
tee -a /usr/share/anaconda/interactive-defaults.ks <<EOF
ostreecontainer --url=$IMAGE_REF:$IMAGE_TAG --transport=containers-storage --no-signature-verification
%include /usr/share/anaconda/post-scripts/install-configure-upgrade.ks
%include /usr/share/anaconda/post-scripts/secureboot-enroll-key.ks
EOF

# Signed Images
tee /usr/share/anaconda/post-scripts/install-configure-upgrade.ks <<EOF
%post --erroronfail
bootc switch --mutate-in-place --enforce-container-sigpolicy --transport registry $IMAGE_REF:$IMAGE_TAG
%end
EOF

tee /usr/local/bin/trivalent-webui <<EOF
#!/bin/bash
exec /usr/bin/trivalent --app="$1" --user-data-dir=/tmp/anaconda-trivalent-profile  --disable-infobars --no-first-run --kiosk "$@"
EOF
chmod 755 /usr/local/bin/trivalent-webui