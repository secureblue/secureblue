#!/usr/bin/env bash

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

if grep -q '^/var/home ' /etc/selinux/targeted/contexts/files/file_contexts.subs_dist; then
    echo "Bad file context (aliasing /var/home) found in file_contexts.subs_dist."
    echo "This is a bug that we're still trying to track down."
    echo "Making build fail to ensure this doesn't silently slip through."
    exit 1
fi
