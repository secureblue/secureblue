#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# /usr/etc/ is an implementation detail of bootc, but we still need a reliable
# baseline of /etc/ for our runtime tooling. bootc does not support having both
# /etc/ and /usr/etc/ populated in an image (undefined behaviour), so instead we
# explicitly make a backup in /usr/share/secureblue/etc/.

cp -a /etc /usr/share/secureblue/
