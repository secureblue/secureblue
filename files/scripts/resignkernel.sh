#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

find /tmp/rpms

KERNEL_VERSION="$(rpm -q "kernel" --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"
RELEASE="$(rpm -E '%fedora.%_arch')"

mkdir "./certs"
PUBLIC_KEY_DER_PATH="./certs/public_key.der"
PUBLIC_KEY_CRT_PATH="./certs/public_key.crt"
PRIVATE_KEY_PATH="./certs/private_key.priv"

openssl x509 -in "$PUBLIC_KEY_DER_PATH" -out "$PUBLIC_KEY_CRT_PATH"
sbsign --cert "$PUBLIC_KEY_CRT_PATH" --key "$PRIVATE_KEY_PATH" /usr/lib/modules/"${KERNEL_VERSION}"/vmlinuz --output /usr/lib/modules/"${KERNEL_VERSION}"/vmlinuz
sbverify --list /usr/lib/modules/"${KERNEL_VERSION}"/vmlinuz

if [[ "$IMAGE_NAME" == *"nvidia"* ]]; then
    curl -Lo /etc/yum.repos.d/negativo17-fedora-multimedia.repo https://negativo17.org/repos/fedora-multimedia.repo
    sed -i '0,/enabled=1/{s/enabled=1/enabled=1\npriority=90/}' /etc/yum.repos.d/negativo17-fedora-multimedia.repo

    dnf install -y akmod-nvidia*.fc${RELEASE}

    KERNEL_MODULE_TYPE="kernel"
    if [[ "$IMAGE_NAME" == *"open"* ]]; then
        KERNEL_MODULE_TYPE+="-open"
    fi

    sed -i "s/^MODULE_VARIANT=.*/MODULE_VARIANT=$KERNEL_MODULE_TYPE/" /etc/nvidia/kernel.conf
    akmods --force --kernels "${KERNEL_VERSION}" --kmod "nvidia"

    modinfo /usr/lib/modules/${KERNEL_VERSION}/extra/nvidia/nvidia{,-drm,-modeset,-peermem,-uvm}.ko.xz > /dev/null || \
        (cat /var/cache/akmods/nvidia/${NVIDIA_AKMOD_VERSION}-for-${KERNEL_VERSION}.failed.log && exit 1)

    # View license information
    modinfo -l /usr/lib/modules/${KERNEL_VERSION}/extra/nvidia/nvidia{,-drm,-modeset,-peermem,-uvm}.ko.xz


    PUBLIC_CHAIN="./certs/public_key_chain.pem"
    SIGNING_KEY="./certs/signing_key.pem"

    cat $PRIVATE_KEY_PATH <(echo) $PUBLIC_KEY_CRT_PATH >> $SIGNING_KEY
    # Sign nvidia
    for module in /usr/lib/modules/"${KERNEL_VERSION}"/extra/nvidia/*.ko*; do
        if [[ "$module_suffix" == ".xz" ]]; then
            xz --decompress "$module"
            openssl cms -sign -signer "${SIGNING_KEY}" -binary -in "nvidia" -outform DER -out "nvidia.cms" -nocerts -noattr -nosmimecap
            /usr/src/kernels/"${KERNEL_VERSION}"/scripts/sign-file -s "nvidia.cms" sha256 "${PUBLIC_KEY_CRT_PATH}" "nvidia"
            ./sign-check.sh "${KERNEL_VERSION}" "nvidia" "${PUBLIC_KEY_CRT_PATH}"
            xz -f "${module_basename}"
        fi
    done