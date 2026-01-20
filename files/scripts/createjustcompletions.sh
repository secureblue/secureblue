#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

umask 022

mkdir -p /usr/share/bash-completion/completions
just --completions bash | sed -E 's/([\(_" ])just\>/\1ujust/g' > /usr/share/bash-completion/completions/ujust

mkdir -p /usr/share/fish/vendor_completions.d
just --completions fish | sed -E 's/([\(_" ])just\>/\1ujust/g' > /usr/share/fish/vendor_completions.d/ujust.fish
