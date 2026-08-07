#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail
shopt -s nullglob
cd "$(dirname "$0")"

github_repo_owner="secureblue"
github_repo_name="secureblue"
ghcr_tag="br-testing-44-uki"

if [[ $(id -u) -ne 0 ]]; then
    echo "The installer must be run as root."
    exit 1
fi

total_ram_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
if [[ "${total_ram_kb}" -lt 3800000 ]]; then
    echo "The installer requires at least 4 GB of RAM."
    exit 1
fi

# Select an image.
valid_images=(
    silverblue-main-hardened
    kinoite-main-hardened
    sericea-main-hardened
    cosmic-main-hardened
    iot-main-hardened
    securecore-main-hardened
)
clear
echo "Choose an image to install:"
printf -- "- %s\n" "${valid_images[@]}"
read -r -p "Enter a full image name: " ghcr_image
valid=0
for image in "${valid_images[@]}"; do
    if [[ "${ghcr_image}" == "${image}" ]]; then
        valid=1
        break
    fi
done
if [[ "${valid}" -ne 1 ]]; then
    echo "Invalid image."
    exit 1
fi
image_ref="ghcr.io/${github_repo_owner}/${ghcr_image}:${ghcr_tag}"

# The CoreOS installer has a permissive container policy by default.
mkdir -p /etc/pki/containers
cp ../cosign.pub "/etc/pki/containers/${github_repo_owner}.pub"
cat > /etc/containers/policy.json << EOF
{
    "default": [{"type": "reject"}],
    "transports": {
        "docker": {
            "ghcr.io/${github_repo_owner}": [
                {
                    "type": "sigstoreSigned",
                    "keyPath": "/etc/pki/containers/${github_repo_owner}.pub",
                    "signedIdentity": {"type": "matchRepository"}
                }
            ]
        }
    }
}
EOF
cat > /etc/containers/registries.d/secureblue.yaml << EOF
docker:
  ghcr.io/${github_repo_owner}:
    use-sigstore-attachments: true
EOF

# Get slsa-verifier.
slsa_verifier_version="2.7.1"
slsa_verifier_sha256="946dbec729094195e88ef78e1734324a27869f03e2c6bd2f61cbc06bd5350339"
crane_version="0.21.7"
crane_sha256="1a57bc98207fa1c0d04bf760699099e26f8383499bfd55b99c1b919a928a7230"
curl -fLsS -o /usr/local/bin/slsa-verifier \
    "https://github.com/slsa-framework/slsa-verifier/releases/download/v${slsa_verifier_version}/slsa-verifier-linux-amd64"
echo "${slsa_verifier_sha256}  /usr/local/bin/slsa-verifier" | sha256sum -c -
chmod +x /usr/local/bin/slsa-verifier

# Get crane.
crane_tarball=$(mktemp)
curl -fLsS -o "${crane_tarball}" \
    "https://github.com/google/go-containerregistry/releases/download/v${crane_version}/go-containerregistry_Linux_x86_64.tar.gz"
echo "${crane_sha256}  ${crane_tarball}" | sha256sum -c -
tar -xzf "${crane_tarball}" -C /usr/local/bin crane
rm -f "${crane_tarball}"

# Get digest and verify provenance.
full_ref=$(crane digest --full-ref "${image_ref}")
slsa-verifier verify-image --source-uri "github.com/${github_repo_owner}/${github_repo_name}" "${full_ref}"

# Partition the disk.
esp_uuid=$(systemd-id128 new --uuid)
root_uuid=$(systemd-id128 new --uuid)
mkdir -p /run/repart.d
cat > /run/repart.d/01-esp.conf << EOF
[Partition]
Type=esp
Format=vfat
UUID=${esp_uuid}
SizeMinBytes=2G
SizeMaxBytes=2G
EOF
cat > /run/repart.d/02-sysroot.conf << EOF
[Partition]
Type=root
Format=btrfs
UUID=${root_uuid}
SizeMinBytes=20G
Encrypt=key-file
EOF

clear
lsblk
echo
echo "Choose a disk to install to, e.g. /dev/vda, /dev/sda or /dev/nvme0n1."
echo "This will erase the disk."
read -r -p "Enter disk: " disk
if [[ ! -b "${disk}" ]] || [[ $(lsblk -ndo TYPE "${disk}") != "disk" ]]; then
    echo "Invalid disk."
    exit 1
fi

echo
echo "Choose a LUKS encryption password."
read -r -s -p "Password: " password && echo
read -r -s -p "Confirm: " password2 && echo
if [[ "${password}" == "${password2}" ]]; then
    keyfile=$(mktemp)
    printf "%s" "${password}" > "${keyfile}"
else
    echo "Passwords do not match."
    exit 1
fi
unset password password2

cleanup() {
    # Clean up /tmp, swap, then /mnt/tmp, then unmount everything else.
    rm -rf /tmp/*
    mount -o remount,size=1G /tmp
    swapoff /mnt/tmp/swap/swapfile || true
    umount /var/lib/containers/storage || true
    rm -rf /mnt/tmp
    sync
    umount /mnt/boot/ || true
    umount /mnt/ || true
    cryptsetup close root || true
}
trap cleanup EXIT
systemd-repart --dry-run=no --empty=force "--key-file=${keyfile}" "${disk}"
udevadm settle
sleep 1

# Mount the partitions.
cryptsetup open "--key-file=${keyfile}" "/dev/disk/by-partuuid/${root_uuid}" root
mount /dev/mapper/root /mnt/
mkdir /mnt/boot/
mount "/dev/disk/by-partuuid/${esp_uuid}" /mnt/boot/

# Use /mnt/tmp as a temporary download location, rather than using RAM.
mkdir -p /mnt/tmp/storage
mount --bind /mnt/tmp/storage /var/lib/containers/storage
chcon "system_u:object_r:container_var_lib_t:s0" /var/lib/containers/storage
mkdir /mnt/tmp/tmp
export TMPDIR=/mnt/tmp/tmp
mkdir /mnt/tmp/swap
chattr +C /mnt/tmp/swap
fallocate -l 4G /mnt/tmp/swap/swapfile
chmod 0600 /mnt/tmp/swap/swapfile
mkswap /mnt/tmp/swap/swapfile
swapon /mnt/tmp/swap/swapfile
mount -o remount,size=8G /tmp
mkdir /mnt/tmp/empty

# Pull the image.
clear
echo "Downloading secureblue..."
podman pull "${full_ref}"

# Perform the installation.
clear
echo "Installing secureblue, this may take some time..."
podman run --rm --privileged --pid=host --ipc=host \
    --security-opt label=type:unconfined_t \
    -v /var/lib/containers:/var/lib/containers \
    -v /dev:/dev \
    -v /:/run/host \
    -v /mnt/tmp/empty:/run/host/mnt/tmp \
    -v "/etc/pki/containers/${github_repo_owner}.pub:/etc/pki/containers/${github_repo_owner}.pub:ro" \
    -v /etc/containers/policy.json:/etc/containers/policy.json:ro \
    "${full_ref}" \
    bootc install to-filesystem \
        "--source-imgref=registry:${full_ref}" \
        "--target-imgref=${image_ref}" \
        --bootloader=systemd --composefs-backend --skip-finalize \
        /run/host/mnt/

# Configure systemd-boot timeout.
sed -i 's/#timeout 3/timeout 3/' /mnt/boot/loader/loader.conf

# Add boot.mount (systemd-gpt-auto-generator doesn't work with composefs+LUKS).
# In future, something like Anaconda will do all of this.
etc_dirs=(/mnt/state/deploy/*/etc)
if [[ ${#etc_dirs[@]} -ne 1 ]]; then
    echo "Expected only one deployment, found ${#etc_dirs[@]}."
    exit 1
fi
etc_dir=${etc_dirs[0]}
escaped_esp="$(systemd-escape -p "/dev/disk/by-partuuid/${esp_uuid}")"
cat > "${etc_dir}/systemd/system/boot.mount" << EOF
[Unit]
Description=EFI System Partition
Requires=systemd-fsck@${escaped_esp}.service
After=systemd-fsck@${escaped_esp}.service
After=blockdev@${escaped_esp}.target

[Mount]
What=/dev/disk/by-partuuid/${esp_uuid}
Where=/boot
Type=vfat
Options=fmask=0177,dmask=0077,rw,nodev,nosuid,noexec

[Install]
WantedBy=local-fs.target
EOF
mkdir -p "${etc_dir}/systemd/system/local-fs.target.wants"
ln -s /etc/systemd/system/boot.mount "${etc_dir}/systemd/system/local-fs.target.wants/boot.mount"

# Create user.
clear
echo "Enter the details of your login account. It will be added to the admin (wheel) group."
echo "You should NOT choose a system username, like 'root' or 'admin'."
echo "Your password will be set to 'secureblue'. You must change it after logging in."
echo
read -r -p "Username: " username
password=$(openssl passwd -6 "secureblue")
last_changed=$(( $(date +%s) / 86400 ))
echo "${username}:x:1000:1000:${username}:/var/home/${username}:/bin/bash" >> "${etc_dir}/passwd"
echo "${username}:${password}:${last_changed}:0:99999:7:::" >> "${etc_dir}/shadow"
echo "${username}:x:1000:" >> "${etc_dir}/group"
sed -i "s/^wheel:x:10:$/&${username}/" "${etc_dir}/group"
var_dir="/mnt/state/os/default/var"
mkdir -p "${var_dir}/home/${username}/"
cp -a "${etc_dir}/skel/." "${var_dir}/home/${username}/"
chown -R 1000:1000 "${var_dir}/home/${username}"
chmod 0700 "${var_dir}/home/${username}"

# Optionally install shim.
clear
cat << 'EOF'
Choose a secure boot option:

1. shim - Safe for all devices.
   Your firmware must trust the Microsoft Third Party CA, which signs many
   bootloaders and ROMs. This greatly increases attack surface but is compatible
   with all hardware.

2. secureblue Platform Key - WARNING: Not suitable for all devices.
   Your firmware will only trust secureblue. This offers improved security, but
   this can BRICK YOUR DEVICE by breaking the display if your external GPU
   requires an option ROM to work.

EOF
read -r -p "Choose an option (1 or 2): " secure_boot
if [[ "${secure_boot}" != "2" ]]; then
    if [[ "${secure_boot}" != "1" ]]; then
        echo "Invalid selection; defaulting to shim."
    fi
    shim_dirs=(/usr/lib/efi/shim/*/EFI)
    if [[ ${#shim_dirs[@]} -ne 1 ]]; then
        echo "Expected only one shim installation, found ${#shim_dirs[@]}."
        exit 1
    fi
    shim_dir=${shim_dirs[0]}
    # BOOT/{BOOTX64.EFI, fbx64.efi, etc.}
    cp "${shim_dir}"/BOOT/* /mnt/boot/EFI/BOOT/
    # fedora/{shim.efi, shimx64.efi, BOOTX64.CSV, mmx64.efi, etc.}
    cp -r "${shim_dir}"/fedora /mnt/boot/EFI/
    # Put MokManager in BOOT/.
    cp "${shim_dir}"/fedora/mmx64.efi /mnt/boot/EFI/BOOT/
    # Rename systemd-boot to grubx64.efi as this is hardcoded into shim.
    mv /mnt/boot/EFI/systemd/systemd-bootx64.efi /mnt/boot/EFI/fedora/grubx64.efi
    rmdir /mnt/boot/EFI/systemd
    # We need to import the key that signed systemd-boot.
    printf "secureblue\nsecureblue\n" | mokutil --import keys/db/db.der > /dev/null
fi

cleanup

# Reboot the system.
clear
cat << EOF
Installation is finished.

Username: ${username}
Password: secureblue

EOF
if [[ "${secure_boot}" == "1" ]]; then
cat << EOF
When the system reboots, you need to choose "Enroll MOK" and enter "secureblue"
as the password.
EOF
else
cat << 'EOF'
After logging in, you must run `ujust enroll-secure-boot-key` to finish setting
up secure boot.

Make sure your device is in Setup Mode first by deleting the Platform Key in
your UEFI settings.

EOF
fi
read -r -p "Press enter to reboot or Ctrl+C to exit to terminal."
systemctl reboot
