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

SUDO_PACKAGES_TO_REMOVE=()

if [[ "$IMAGE_NAME" != *"kinoite"* ]]; then
    SUDO_PACKAGES_TO_REMOVE+=('sudo')
fi

if [[ "$IMAGE_NAME" == *"iot"* && "$OS_ARCH" == "aarch64" ]]; then
    SUDO_PACKAGES_TO_REMOVE+=('arm-image-installer')
fi

if [[ "$IMAGE_NAME" != *"iot"* && "$IMAGE_NAME" != *"securecore"* ]]; then
    SUDO_PACKAGES_TO_REMOVE+=('sudo-python-plugin')
fi

dnf remove -y --setopt=protected_packages=, "${SUDO_PACKAGES_TO_REMOVE[@]}"

rm -rf /usr/bin/sudo
