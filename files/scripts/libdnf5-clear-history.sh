#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail
shopt -s nullglob

# dnf transaction history is a source of non-reproducibility between builds.
# The upstream base images leave this directory entirely empty. We avoid
# deleting the lockfile because that currently triggers a bug in dnf5:
# https://github.com/rpm-software-management/dnf5/issues/2709
#
# Note: this causes `dnf history list` and similar commands to fail. That isn't
# a useful command anyway right now, but at some point in the future, if dnf
# adds support for local layering, we will probably need to remove this.
rm -f /usr/lib/sysimage/libdnf5/{*.toml,transaction_history.sqlite*}
