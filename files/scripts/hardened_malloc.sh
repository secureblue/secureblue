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

set -euo pipefail

env_file='/etc/environment'

# Create the env file if it doesn't already exist
if [[ ! -f "${env_file}" ]]; then
    echo '' > "${env_file}"
fi

# Remove any existing LD_PRELOAD entries and append LD_PRELOAD to end of file
sed -i -e '$a\LD_PRELOAD=libhardened_malloc.so' -e '/^[[:space:]]*LD_PRELOAD=/d' "${env_file}"
