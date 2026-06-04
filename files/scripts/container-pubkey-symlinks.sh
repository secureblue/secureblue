#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Symlink container public keys from /etc/pki/containers to /usr/share/pki/containers to ensure
# that image signature verification doesn't break for users with local modifications to
# /etc/containers/policy.json (who won't automatically get policy updates).
for pubkey in /usr/share/pki/containers/*.pub; do
    ln -s "${pubkey}" "/etc${pubkey#/usr/share}"
done
