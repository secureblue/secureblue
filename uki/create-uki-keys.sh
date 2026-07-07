#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# This script creates secure boot keys (a platform key, a key exchange key and
# database key). These, alongside Microsoft's certificates, are converted to EFI
# signature lists, and (self-)signed to produce authenticated variables that can
# be enrolled in the firmware.

cd "$(dirname "$0")"

mkdir keys/
uuid=$(systemd-id128 new --uuid)
echo "${uuid}" > keys/GUID

for key in PK KEK db; do
  mkdir "keys/${key}"

  # Make new secure boot keys (PK, KEK, db).
  openssl req -new -x509 -nodes -subj "/CN=secureblue ${key} CA $(date +%Y)/" \
    -keyout "keys/${key}/${key}.key" -out "keys/${key}/${key}.pem" &> /dev/null
  openssl x509 -outform DER -in "keys/${key}/${key}.pem" -out "keys/${key}/${key}.der"

  # Convert to an EFI signature list.
  sbsiglist --owner "${uuid}" --type x509 \
    --output "keys/${key}/${key}.esl" "keys/${key}/${key}.der"
done

# Now sign the EFI signature lists. The PK is a self-signed payload, and it
# signs the KEK, which signs the db. This attribute is standard.
attr=NON_VOLATILE,RUNTIME_ACCESS,BOOTSERVICE_ACCESS,TIME_BASED_AUTHENTICATED_WRITE_ACCESS
sbvarsign --attr "${attr}" --key keys/PK/PK.key --cert keys/PK/PK.pem \
  --output "keys/PK/PK.auth" PK keys/PK/PK.esl
sbvarsign --attr "${attr}" --key keys/PK/PK.key --cert keys/PK/PK.pem \
  --output "keys/KEK/KEK.auth" KEK keys/KEK/KEK.esl
sbvarsign --attr "${attr}" --key keys/KEK/KEK.key --cert keys/KEK/KEK.pem \
  --output "keys/db/db.auth" db keys/db/db.esl

echo "Please back up your keys:"
echo " - \"$(pwd)/keys/PK/PK.key\","
echo " - \"$(pwd)/keys/KEK/KEK.key\","
echo " - \"$(pwd)/keys/db/db.key\" (upload to GitHub as the UKI_DB_KEY secret),"
echo "and commit the generated .auth, .der and .pem files to the repository."
