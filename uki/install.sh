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

if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "This script must be run as root."
    exit 1
fi

valid_images=(
    silverblue-main-hardened
    kinoite-main-hardened
    sericea-main-hardened
    cosmic-main-hardened
    iot-main-hardened
    securecore-main-hardened
)
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
esp_uuid=$(uuidgen)
root_uuid=$(uuidgen)
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

lsblk
echo "Choose a disk to install to, e.g. /dev/vda, /dev/sda or /dev/nvme0n1."
echo "This will erase the disk."
read -r -p "Enter disk: " disk
if [[ ! -b "${disk}" ]] || [[ $(lsblk -ndo TYPE "${disk}") != "disk" ]]; then
    echo "Invalid disk."
    exit 1
fi

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
    rm -f "${keyfile}"
    umount /var/lib/containers/storage/ || true
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

# Pull the image.
mount -t tmpfs -o size=10240M containers /var/lib/containers/storage/
chcon "system_u:object_r:container_var_lib_t:s0" /var/lib/containers/storage
podman pull "${full_ref}"

# Perform the installation.
podman run --rm --privileged --pid=host --ipc=host \
    --security-opt label=type:unconfined_t \
    -v /var/lib/containers:/var/lib/containers -v /dev:/dev \
    -v /:/run/host \
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

# Optionally install shim.
cat << EOF
Choose a secure boot option:
1. shim - Safe for all devices.
   Your firmware must trust the Microsoft Third Party CA, which signs many
   bootloaders and ROMs. This greatly increases attack surface but is compatible
   with all hardware.
2. secureblue Platform Key - Suitable for some devices.
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
    printf "secureblue\nsecureblue\n" | mokutil --import keys/db/db.der
fi

sync

# Reboot the system.
if [[ "${secure_boot}" == "1" ]]; then
    echo "Installation is finished. When the system reboots, you need to choose"
    echo "\"Enroll MOK\" and enter \"secureblue\" as the password."
else
    echo "Installation is finished. Make sure your device is in Setup Mode by deleting"
    echo "the Secure Boot Platform Key in your UEFI settings."
fi
read -r -p "Press enter to reboot."
systemctl reboot
