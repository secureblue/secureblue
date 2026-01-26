#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# dnf transaction history is a source of non-reproducibility between builds.
# The upstream base images also leave this directory empty.
# Note: this causes `dnf history list` and similar commands to fail. That isn't
# a useful command anyway right now, but at some point in the future, if dnf
# adds support for local layering, we will probably need to remove this.
find /usr/lib/sysimage/libdnf5 -mindepth 1 -delete
