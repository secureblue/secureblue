#!/usr/bin/env bash

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



if [[ "$IMAGE_NAME" != *"securecore"* ]]; then
  KERNEL_VERSION="6.17.12-300"
  KERNEL_HEADERS_VERSION="6.17.4-300"
  
  dnf install -y --from-repo=updates-archive \
    "kernel-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-core-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-modules-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-modules-core-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-modules-extra-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-tools-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-tools-libs-${KERNEL_VERSION}.fc${OS_VERSION}" \
    "kernel-headers-${KERNEL_HEADERS_VERSION}.fc${OS_VERSION}"
fi