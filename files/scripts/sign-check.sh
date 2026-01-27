#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

KERNEL="$1"
module="$2"
PUBLIC_CERT="$3"

kmod_sig="/tmp/kmod.sig"
kmod_p7s="/tmp/kmod.p7s"
kmod_data="/tmp/kmod.data"
/usr/src/kernels/"${KERNEL}"/scripts/extract-module-sig.pl -s "${module}" > "${kmod_sig}"
openssl pkcs7 -inform der -in "${kmod_sig}" -out "${kmod_p7s}"
/usr/src/kernels/"${KERNEL}"/scripts/extract-module-sig.pl -0 "${module}" > "${kmod_data}"
if openssl cms -verify -binary -inform PEM \
    -in "${kmod_p7s}" \
    -content "${kmod_data}" \
    -certfile "${PUBLIC_CERT}" \
    -out "/dev/null" \
    -nointern -noverify
    then
    echo "Signature Verified for ${module}"
else
    echo "Signature Failed for ${module}"
    exit 1
fi