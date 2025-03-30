#!/usr/bin/env bash

# Copyright 2025 Universal Blue
# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

set -oue pipefail

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