#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# This script generates the secrets needed for a secureblue development fork,
# makes the necessary config changes for builds to work, and disables
# unnecessary scheduled workflows.

# Run in the repository root.
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

# We'll create secrets/{cosign, MOK, PK, KEK, db, pcr}.key.
if [[ -d secrets/ ]]; then
  echo "A secrets directory already exists. Would you like to overwrite them?"
  read -r -p "Continue? [y/N]: " answer
  [[ ${answer} =~ ^[Yy] ]] || exit 0
fi
mkdir -p secrets/

# Generate the cosign key.
# `cosign generate-key-pair` uses prime256v1 (ECDSA P-256) by default,
# optionally encrypted with a passphrase, which we don't need.
openssl ecparam -name prime256v1 -genkey -noout -out secrets/cosign.key
openssl ec -in secrets/cosign.key -pubout -out cosign.pub

# Generate the MOK (akmods) key.
date="$(date -I)"
openssl req -new -x509 -nodes -subj "/CN=secureblue Test MOK CA ${date}/" \
  -keyout secrets/MOK.key -out files/system/usr/share/pki/akmods/certs/akmods-secureblue.der \
  -outform DER &> /dev/null

# Generate the UKI keys (secure boot PK, KEK and db, and the PCR signing
# keypair), replacing the upstream ones, then move the private keys to secrets/.
rm -rf uki/keys/
uki/create-uki-keys.sh > /dev/null
for key in PK KEK db pcr; do
  mv "uki/keys/${key}/${key}.key" "secrets/${key}.key"
done

# Replace instances of RoyalOughtness with the user's GitHub username.
read -r -p "Enter your GitHub username (e.g. royaloughtness): " username
sed --sandbox -i "s/royaloughtness/${username}/g" .github/workflows/*.yml
sed --sandbox -i "s/royaloughtness/${username}/gi" .github/CODEOWNERS

# Apply patches (e.g. remove schedule trigger on workflows).
git apply tools/dev-patches/*.patch

cat << EOF
Please back up all your keys, found in the secrets/ directory.
Commit the generated .auth, .der and .pem files to the repository.
Upload the following secrets to GitHub by copy-pasting the file contents:
- SIGNING_SECRET - "${PWD}/secrets/cosign.key"
- KERNEL_PRIVKEY - "${PWD}/secrets/MOK.key"
- UKI_DB_KEY     - "${PWD}/secrets/db.key"
- UKI_PCR_KEY    - "${PWD}/secrets/pcr.key"
EOF
