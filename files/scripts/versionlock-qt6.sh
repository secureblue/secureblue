#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Prevent broken Qt6 updates if it's updated in the repos more recently than
# the last base image build.

dnf versionlock add 'qt6-*'
