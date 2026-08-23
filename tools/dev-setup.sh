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

# We'll create secrets/{cosign, MOK, PK, KEK, db}.key.
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

# Generate UKI secure boot keys: PK, KEK and db.
mkdir -p uki/keys/
uuid=$(systemd-id128 new --uuid)
echo "${uuid}" > uki/keys/GUID

for key in PK KEK db; do
  mkdir "uki/keys/${key}"

  openssl req -new -x509 -nodes -subj "/CN=secureblue Test ${key} CA ${date}/" \
    -keyout "secrets/${key}.key" -out "uki/keys/${key}/${key}.pem" &> /dev/null
  openssl x509 -outform DER -in "uki/keys/${key}/${key}.pem" -out "uki/keys/${key}/${key}.der"

  # Convert to an EFI signature list.
  sbsiglist --owner "${uuid}" --type x509 \
    --output "uki/keys/${key}/${key}.esl" "uki/keys/${key}/${key}.der"
done

# Produce authenticated variables for enrolment in the firmware.
# The PK is self-signed, which signs the KEK, which signs the db.
attr=NON_VOLATILE,RUNTIME_ACCESS,BOOTSERVICE_ACCESS,TIME_BASED_AUTHENTICATED_WRITE_ACCESS
sbvarsign --attr "${attr}" --key secrets/PK.key --cert uki/keys/PK/PK.pem \
  --output uki/keys/PK/PK.auth PK uki/keys/PK/PK.esl
sbvarsign --attr "${attr}" --key secrets/PK.key --cert uki/keys/PK/PK.pem \
  --output uki/keys/KEK/KEK.auth KEK uki/keys/KEK/KEK.esl
sbvarsign --attr "${attr}" --key secrets/KEK.key --cert uki/keys/KEK/KEK.pem \
  --output uki/keys/db/db.auth db uki/keys/db/db.esl

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
EOF
