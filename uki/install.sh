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

# Check prerequisites.
if [[ $(id -u) -ne 0 ]]; then
    echo "The installer must be run as root."
    exit 1
fi
total_ram_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
if [[ "${total_ram_kb}" -lt 3800000 ]]; then
    echo "The installer requires at least 4 GB of RAM."
    exit 1
fi

# Ask the user to select an image.
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

# The CoreOS installer has a permissive container policy by default. We modify
# it to verify the cosign signature of the selected image.
mkdir -p /etc/pki/containers
cp ../cosign.pub /etc/pki/containers/secureblue.pub
cat > /etc/containers/policy.json << EOF
{
    "default": [{"type": "reject"}],
    "transports": {
        "docker": {
            "ghcr.io/${github_repo_owner}": [
                {
                    "type": "sigstoreSigned",
                    "keyPath": "/etc/pki/containers/secureblue.pub",
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

# Get digest of selected image and verify provenance.
full_ref=$(crane digest --full-ref "${image_ref}")
slsa-verifier verify-image --source-uri "github.com/${github_repo_owner}/${github_repo_name}" "${full_ref}"

# Display available block devices and ask the user to select one.
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
if [[ $(lsblk -o SIZE -bnd "${disk}") -lt 30000000000 ]]; then
    echo "Disk must have a size of at least 32 GB."
    exit 1
fi

# Ask the user for a LUKS encryption password for FDE on the root partition.
echo
read -r -p "Would you like to configure disk encryption? [Y/n] " luks
if [[ ! "${luks}" =~ ^[Nn] ]]; then
    echo "Choose a LUKS encryption password."
    read -r -s -p "Password: " password && echo
    read -r -s -p "Confirm: " password2 && echo
    if [[ "${password}" == "${password2}" ]]; then
        keyfile=$(mktemp)
        printf "%s" "${password}" > "${keyfile}"
        unset password password2
    else
        echo "Passwords do not match."
        exit 1
    fi
fi

# Trap to clean up mounts that we set up later.
cleanup() {
    # We expand /tmp to 8G later, so we need to clear it then shrink it to avoid
    # OOMing when the swapfile is disabled.
    rm -rf /tmp/*
    mount -o remount,size=1G /tmp
    # Disable the swapfile.
    swapoff /mnt/tmp/swap/swapfile || true
    # Delete the swapfile, TMPDIR and container storage created on the disk.
    umount /var/lib/containers/storage || true
    rm -rf /mnt/tmp
    # Now clean up remaining mounts.
    sync
    umount /mnt/boot/ || true
    umount /mnt/ || true
    cryptsetup close root || true
}
trap cleanup EXIT

# Partition the installation disk.
wipefs -a "${disk}"
sgdisk --zap-all "${disk}"

esp_uuid=$(systemd-id128 new --uuid)
root_uuid=$(systemd-id128 new --uuid)
sgdisk --new=1:2048:+2G \
    --typecode=1:ef00 \
    --change-name=1:"esp" \
    --partition-guid=1:"${esp_uuid}" \
    "${disk}"
# Note: typecode 8304 is x86-64 specific.
sgdisk --largest-new=2 \
    --typecode=2:8304 \
    --change-name=2:"root-x86-64" \
    --partition-guid=2:"${root_uuid}" \
    "${disk}"
udevadm settle

wipefs -a "/dev/disk/by-partuuid/${root_uuid}"
wipefs -a "/dev/disk/by-partuuid/${esp_uuid}"

if [[ ! "${luks}" =~ ^[Nn] ]]; then
    cryptsetup luksFormat -q "/dev/disk/by-partuuid/${root_uuid}" "${keyfile}"
    cryptsetup open "--key-file=${keyfile}" "/dev/disk/by-partuuid/${root_uuid}" root
    mkfs.btrfs /dev/mapper/root
else
    mkfs.btrfs --force "/dev/disk/by-partuuid/${root_uuid}"
fi

mkfs.vfat -F 32 "/dev/disk/by-partuuid/${esp_uuid}"
udevadm settle

# Mount the installation partitions to /mnt and /mnt/boot.
if [[ ! "${luks}" =~ ^[Nn] ]]; then
    mount /dev/mapper/root /mnt/
else
    mount "/dev/disk/by-partuuid/${root_uuid}" /mnt/
fi
mkdir /mnt/boot/
mount "/dev/disk/by-partuuid/${esp_uuid}" /mnt/boot/

# To reduce the RAM requirement, we can use the installation disk for temporary
# storage in /mnt/tmp, and clean it up afterwards.
# Use the disk for container storage for podman (for the downloaded image).
mkdir -p /mnt/tmp/storage
mount --bind /mnt/tmp/storage /var/lib/containers/storage
chcon "system_u:object_r:container_var_lib_t:s0" /var/lib/containers/storage
# During the download of the image, a large $TMPDIR is needed.
mkdir /mnt/tmp/tmp
export TMPDIR=/mnt/tmp/tmp
# To provide additional buffer, create a 4G swapfile on the disk.
mkdir /mnt/tmp/swap
chattr +C /mnt/tmp/swap
fallocate -l 4G /mnt/tmp/swap/swapfile
chmod 0600 /mnt/tmp/swap/swapfile
mkswap /mnt/tmp/swap/swapfile
swapon /mnt/tmp/swap/swapfile
# With the swap space, we can expand the /tmp tmpfs to 4G as well.
mount -o remount,size=4G /tmp
mkdir /mnt/tmp/empty

# Pull the secureblue image.
clear
echo "Downloading secureblue..."
podman pull "${full_ref}"

# Perform the installation.
clear
echo "Installing secureblue, this may take some time..."
# We need to mask /mnt/tmp with an empty directory, as bootc validates that
# the installation target only contains mountpoints.
podman run --rm --privileged --pid=host --ipc=host \
    --security-opt label=type:unconfined_t \
    -v /:/run/host \
    -v /dev:/dev \
    -v /mnt/tmp/empty:/run/host/mnt/tmp \
    -v /var/lib/containers:/var/lib/containers \
    -v "/etc/pki/containers/secureblue.pub:/etc/pki/containers/secureblue.pub:ro" \
    -v /etc/containers/policy.json:/etc/containers/policy.json:ro \
    "${full_ref}" \
    bootc install to-filesystem \
        "--source-imgref=registry:${full_ref}" \
        "--target-imgref=${image_ref}" \
        --bootloader=systemd --composefs-backend --skip-finalize \
        /run/host/mnt/

# Configure systemd-boot on the target system to give a GRUB-like menu to select
# the desired bootc deployment (e.g. for rollback).
sed -i 's/#timeout 3/timeout 3/' /mnt/boot/loader/loader.conf

# Configure /boot (boot.mount) on the target system. systemd-gpt-auto-generator
# can't automatically do this with composefs+LUKS, so we do it manually.
etc_dirs=(/mnt/state/deploy/*/etc)
if [[ ${#etc_dirs[@]} -ne 1 ]]; then
    echo "Expected only one deployment, found ${#etc_dirs[@]}."
    echo "This is a bug! Report to https://github.com/secureblue/secureblue/issues."
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

# Create the login user on the target system.
clear
cat << EOF
Enter the details of your login account. It will be added to the wheel group.
You should NOT choose a system username, like 'root' or 'admin'.
Your password will be set to 'secureblue'. You must change it after logging in.

EOF
read -r -p "Username: " username
# We use a hardcoded password because yescrypt isn't available here, only
# SHA512, so the user will have to change it themselves after firstrun.
password=$(openssl passwd -6 "secureblue")
last_changed=$(( $(date +%s) / 86400 ))
echo "${username}:x:1000:1000:${username}:/var/home/${username}:/bin/bash" >> "${etc_dir}/passwd"
echo "${username}:${password}:${last_changed}:0:99999:7:::" >> "${etc_dir}/shadow"
# Now add the user to the wheel group.
echo "${username}:x:1000:" >> "${etc_dir}/group"
sed -i "s/^wheel:x:10:$/&${username}/" "${etc_dir}/group"
# Create their home directory using /etc/skel and set correct permissions.
var_dir="/mnt/state/os/default/var"
mkdir -p "${var_dir}/home/${username}/"
cp -a "${etc_dir}/skel/." "${var_dir}/home/${username}/"
chown -R 1000:1000 "${var_dir}/home/${username}"
chmod 0700 "${var_dir}/home/${username}"
# We have to manually set the SELinux contexts, otherwise they'll be etc_t.
chcon -R "unconfined_u:object_r:user_home_t:s0" "${var_dir}/home/${username}"
chcon "unconfined_u:object_r:user_home_dir_t:s0" "${var_dir}/home/${username}"
chcon -R "unconfined_u:object_r:config_home_t:s0" "${var_dir}/home/${username}/.config" || true
chcon -R "unconfined_u:object_r:virt_home_t:s0" "${var_dir}/home/${username}/.config/libvirt" || true

# Optionally install shim.
clear
cat << 'EOF'
Choose a secure boot option:

1. shim - Safe for all devices.
   However, your firmware must trust the Microsoft Third Party CA, which signs
   many bootloaders and ROMs. This greatly increases attack surface but is
   compatible with all hardware.

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
        echo "This is a bug! Report to https://github.com/secureblue/secureblue/issues."
        exit 1
    fi
    shim_dir=${shim_dirs[0]}

    # Install shim.
    # Install the shim EFI binaries.
    cp "${shim_dir}"/BOOT/* /mnt/boot/EFI/BOOT/
    cp -r "${shim_dir}/fedora" /mnt/boot/EFI/
    # mmx64.efi is MokManager, and we want it to run by default.
    cp "${shim_dir}/fedora/mmx64.efi" /mnt/boot/EFI/BOOT/
    # Rename systemd-boot to grubx64.efi as this is hardcoded into shim.
    mv /mnt/boot/EFI/systemd/systemd-bootx64.efi /mnt/boot/EFI/fedora/grubx64.efi
    rmdir /mnt/boot/EFI/systemd
    # systemd-boot was signed with the secureblue MOK, so that needs to be
    # imported before first boot.
    printf "secureblue\nsecureblue\n" | mokutil --import keys/db/db.der > /dev/null
fi

# Everything succeeded, so clean up now to delete /mnt/tmp before firstrun.
cleanup

# Display instructions and reboot the system.
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
After logging in, you must run `ujust enroll-secure-boot-keys` to finish setting
up secure boot.

Make sure your device is in Setup Mode first by deleting the Platform Key in
your UEFI settings.

EOF
fi
read -r -p "Press enter to reboot or Ctrl+C to exit to terminal."
systemctl reboot
