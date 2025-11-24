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

umask 022

mkdir -p /usr/share/bash-completion/completions
just --completions bash | sed -E 's/([\(_" ])just\>/\1ujust/g' > /usr/share/bash-completion/completions/ujust

mkdir -p /usr/share/fish/vendor_completions.d
just --completions fish | sed -E 's/([\(_" ])just\>/\1ujust/g' > /usr/share/fish/vendor_completions.d/ujust.fish
