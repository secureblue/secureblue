#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

MODULE_NAME="${1-}"
if [[ -z "${MODULE_NAME}" ]]; then
  echo 'MODULE_NAME is empty. Exiting...'
  exit 1
fi

KERNEL_VERSION="$(rpm -q 'kernel' --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"

PUBLIC_KEY_DER_PATH='../system/usr/share/pki/akmods/certs/akmods-secureblue.der'
PUBLIC_KEY_CRT_PATH='./certs/public_key.crt'
PRIVATE_KEY_PATH='/tmp/certs/private_key.priv'
openssl x509 -in "${PUBLIC_KEY_DER_PATH}" -out "${PUBLIC_KEY_CRT_PATH}"

PRIVATE_KEY_PATH='/tmp/certs/private_key.priv'
SIGNING_KEY='./certs/signing_key.pem'
cat "${PRIVATE_KEY_PATH}" <(echo) "${PUBLIC_KEY_CRT_PATH}" >> "${SIGNING_KEY}"

sign_module() {
    local module="$1"
    openssl cms -sign -signer "${SIGNING_KEY}" -binary -in "${module}" \
        -outform DER -out "${module}.cms" -nocerts -noattr -nosmimecap
    "/usr/src/kernels/${KERNEL_VERSION}/scripts/sign-file" -s "${module}.cms" \
        sha256 "${PUBLIC_KEY_CRT_PATH}" "${module}"
    /bin/bash ./sign-check.sh "${KERNEL_VERSION}" "${module}" "${PUBLIC_KEY_CRT_PATH}"
}

for module in "/usr/lib/modules/${KERNEL_VERSION}/extra/${MODULE_NAME}"/*.ko*; do
    module_basename="${module%.*}"
    module_suffix=".${module##*.}"
    case "${module_suffix}" in
        .xz)
            xz --decompress "${module}"
            sign_module "${module_basename}"
            xz -C crc32 -f "${module_basename}"
            ;;
        .gz)
            gzip -d "${module}"
            sign_module "${module_basename}"
            gzip -9f "${module_basename}"
            ;;
        *)
            sign_module "${module}"
            ;;
    esac
done
