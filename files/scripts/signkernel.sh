#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

KERNEL_VERSION="$(rpm -q "kernel" --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"

PUBLIC_KEY_DER_PATH="./certs/public_key.der"
PUBLIC_KEY_CRT_PATH="./certs/public_key.crt"
PRIVATE_KEY_PATH="./certs/private_key.priv"

openssl x509 -in "$PUBLIC_KEY_DER_PATH" -out "$PUBLIC_KEY_CRT_PATH"
sbsign --cert "$PUBLIC_KEY_CRT_PATH" --key "$PRIVATE_KEY_PATH" /usr/lib/modules/"${KERNEL_VERSION}"/vmlinuz --output /usr/lib/modules/"${KERNEL_VERSION}"/vmlinuz
sbverify --list /usr/lib/modules/"${KERNEL_VERSION}"/vmlinuz

install -Dm0644 $PUBLIC_KEY_DER_PATH /etc/pki/akmods/certs/akmods-secureblue.der
