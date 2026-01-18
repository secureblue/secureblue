#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -oue pipefail

MODULE_NAME="${1-}"
if [ -z "$MODULE_NAME" ]; then
  echo "MODULE_NAME is empty. Exiting..."
  exit 1
fi

KERNEL_VERSION="$(rpm -q "kernel" --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"

PUBLIC_KEY_DER_PATH="../system/etc/pki/akmods/certs/akmods-secureblue.der"
PUBLIC_KEY_CRT_PATH="./certs/public_key.crt"
PRIVATE_KEY_PATH="/tmp/certs/private_key.priv"
openssl x509 -in "$PUBLIC_KEY_DER_PATH" -out "$PUBLIC_KEY_CRT_PATH"

PRIVATE_KEY_PATH="/tmp/certs/private_key.priv"
SIGNING_KEY="./certs/signing_key.pem"
cat "$PRIVATE_KEY_PATH" <(echo) "$PUBLIC_KEY_CRT_PATH" >> "$SIGNING_KEY"

for module in /usr/lib/modules/"${KERNEL_VERSION}"/extra/"${MODULE_NAME}"/*.ko*; do
    module_basename="${module:0:-3}"
    module_suffix="${module: -3}"
    if [[ "$module_suffix" == ".xz" ]]; then
        xz --decompress "$module"
        openssl cms -sign -signer "${SIGNING_KEY}" -binary -in "$module_basename" -outform DER -out "${module_basename}.cms" -nocerts -noattr -nosmimecap
        /usr/src/kernels/"${KERNEL_VERSION}"/scripts/sign-file -s "${module_basename}.cms" sha256 "${PUBLIC_KEY_CRT_PATH}" "${module_basename}"
        /bin/bash ./sign-check.sh "${KERNEL_VERSION}" "${module_basename}" "${PUBLIC_KEY_CRT_PATH}"
        xz -C crc32 -f "${module_basename}"
    elif [[ "$module_suffix" == ".gz" ]]; then
        gzip -d "$module"
        openssl cms -sign -signer "${SIGNING_KEY}" -binary -in "$module_basename" -outform DER -out "${module_basename}.cms" -nocerts -noattr -nosmimecap
        /usr/src/kernels/"${KERNEL_VERSION}"/scripts/sign-file -s "${module_basename}.cms" sha256 "${PUBLIC_KEY_CRT_PATH}" "${module_basename}"
        /bin/bash ./sign-check.sh "${KERNEL_VERSION}" "${module_basename}" "${PUBLIC_KEY_CRT_PATH}"
        gzip -9f "${module_basename}"
    else
        openssl cms -sign -signer "${SIGNING_KEY}" -binary -in "$module" -outform DER -out "${module}.cms" -nocerts -noattr -nosmimecap
        /usr/src/kernels/"${KERNEL_VERSION}"/scripts/sign-file -s "${module}.cms" sha256 "${PUBLIC_KEY_CRT_PATH}" "${module}"
        /bin/bash ./sign-check.sh "${KERNEL_VERSION}" "${module}" "${PUBLIC_KEY_CRT_PATH}"
    fi
done
