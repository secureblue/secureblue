#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# This script creates the keypair used to sign TPM2 PCR 11 predictions that get
# embedded in the UKI (.pcrsig/.pcrpkey sections). This is a SEPARATE key from
# the Secure Boot db key: compromise of this key lets an attacker forge a
# policy that authorizes unlocking TPM2-bound LUKS volumes, so treat it with at
# least as much care.

cd "$(dirname "$0")"

mkdir -p keys/pcr
ukify genkey \
  --pcr-private-key=keys/pcr/pcr.key \
  --pcr-public-key=keys/pcr/pcr.pub.pem

echo "Please back up your key:"
echo " - \"$(pwd)/keys/pcr/pcr.key\" (upload to GitHub as the UKI_PCR_KEY secret),"
echo "and commit the generated keys/pcr/pcr.pub.pem file to the repository."
