#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# This script creates secure boot keys (a platform key, a key exchange key and
# database key). These are converted to EFI signature lists, and (self-)signed
# to produce authenticated variables that can be enrolled in the firmware.
# It also creates a PCR signing keypair, used to sign the TPM2 PCR 11
# predictions that get embedded in the UKI.

# Run in the repository root.
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

if [[ "${1:-}" == "--dev" ]]; then
  ca_date="$(date -I)"
  ca_expiry_days=365
  ca_title="secureblue Test"
else
  ca_date="$(date +%Y)"
  ca_expiry_days=3650
  ca_title="secureblue"
fi

if [[ "${1:-}" != "--dev" && ( -d uki/keys/ || -d secrets/ ) ]]; then
  echo "A secrets directory already exists in uki/keys/ or secrets/."
  read -r -p "Would you like to overwrite them? [y/N]: " answer
  [[ ${answer} =~ ^[Yy] ]] || exit 1
fi
mkdir -p secrets/
mkdir -p uki/keys/
uuid=$(systemd-id128 new --uuid)
echo "${uuid}" > uki/keys/GUID

# Generate secure boot keys.
for key in PK KEK db; do
  mkdir -p "uki/keys/${key}"

  openssl req -new -x509 -nodes -days "${ca_expiry_days}" \
    -subj "/CN=${ca_title} ${key} CA ${ca_date}/" \
    -keyout "secrets/${key}.key" -out "uki/keys/${key}/${key}.pem" &> /dev/null
  openssl x509 -outform DER -in "uki/keys/${key}/${key}.pem" -out "uki/keys/${key}/${key}.der"

  # Generate EFI signature list from key.
  sbsiglist --owner "${uuid}" --type x509 \
    --output "uki/keys/${key}/${key}.esl" "uki/keys/${key}/${key}.der"
done

# Generate PCR keypair.
mkdir -p uki/keys/PCR
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out secrets/PCR.key
openssl pkey -in secrets/PCR.key -pubout -out uki/keys/PCR/PCR.pem

# Now sign the EFI signature lists. The PK is a self-signed payload, and it
# signs the KEK, which signs the db. This attribute is standard.
attr=NON_VOLATILE,RUNTIME_ACCESS,BOOTSERVICE_ACCESS,TIME_BASED_AUTHENTICATED_WRITE_ACCESS
sbvarsign --attr "${attr}" --key secrets/PK.key --cert uki/keys/PK/PK.pem \
  --output uki/keys/PK/PK.auth PK uki/keys/PK/PK.esl
sbvarsign --attr "${attr}" --key secrets/PK.key --cert uki/keys/PK/PK.pem \
  --output uki/keys/KEK/KEK.auth KEK uki/keys/KEK/KEK.esl
sbvarsign --attr "${attr}" --key secrets/KEK.key --cert uki/keys/KEK/KEK.pem \
  --output uki/keys/db/db.auth db uki/keys/db/db.esl

cat << EOF
Please back up all your keys, found in the secrets/ directory.
Commit the generated .auth, .der and .pem files to the repository.
Upload the following secrets to GitHub by copy-pasting the file contents:
- UKI_DB_KEY     - "${PWD}/secrets/db.key"
- UKI_PCR_KEY    - "${PWD}/secrets/PCR.key"
EOF
