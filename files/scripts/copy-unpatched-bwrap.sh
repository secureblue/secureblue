#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Make a copy of the unpatched bwrap executable before we replace it
cp -p /usr/bin/bwrap /usr/bin/bwrap-original
