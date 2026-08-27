#!/usr/bin/python3

"""Enrolls secure boot keys into shim or the firmware. Should be run as root."""

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import hashlib
import os
import shutil
import struct
import subprocess
import sys
import uuid
from pathlib import Path

from shared.secure_boot import (
    EFI_GUID_SIZE,
    EFI_NS_GLOBAL,
    EFI_NS_SECURITY,
    EFI_NS_SHIM,
    EFI_TYPE_X509,
    EFI_UINT32_SIZE,
    EFIVARS,
    EnrollEfiKeys,
    EnrollMokKey,
    deserialize,
)

# UEFI variable attributes.
EFI_ATTR_NON_VOLATILE = 0x00000001  # EFI_VARIABLE_NON_VOLATILE
EFI_ATTR_BOOTSERVICE = 0x00000002  # EFI_VARIABLE_BOOTSERVICE_ACCESS
EFI_ATTR_RUNTIME = 0x00000004  # EFI_VARIABLE_RUNTIME_ACCESS
EFI_ATTR_TIME_BASED_AUTH_WRITE = 0x00000020  # EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS

SYSTEMD_BOOT_NEW = Path("/usr/lib/systemd/boot/efi/systemd-bootx64.efi")
BOOTLOADER_ESP_BOOT = Path("/boot/EFI/BOOT/BOOTX64.EFI")
BOOTLOADER_ESP_SYSTEMD = Path("/boot/EFI/systemd/systemd-bootx64.efi")


def _write_efi_bytes(variable: str, ns_guid: str, attributes: int, payload: bytes) -> None:
    """Writes a UEFI variable with an attribute."""

    path = EFIVARS / f"{variable}-{ns_guid}"

    # The kernel exposes efivars with the attributes as a 4-byte LE uint at the start.
    data = struct.pack("<I", attributes) + payload

    # Existing efivars are marked immutable, so that needs to be explicitly cleared.
    if path.exists():
        subprocess.run(["/usr/bin/chattr", "-i", path.as_posix()], check=True)

    os.umask(0o022)  # Otherwise the outer function can't verify the PK.
    path.write_bytes(data)

    subprocess.run(["/usr/bin/chattr", "+i", path.as_posix()], check=True)


def enroll_efi_keys(*, db_auth: Path, kek_auth: Path, pk_auth: Path) -> None:
    """Enroll db, KEK, and PK directly into UEFI firmware.

    Args:
        db_auth: The db.auth file in EFI_VARIABLE_AUTHENTICATION_2 format.
        kek_auth: The KEK.auth file in EFI_VARIABLE_AUTHENTICATION_2 format.
        pk_auth: The PK.auth file in EFI_VARIABLE_AUTHENTICATION_2 format.
    """

    # These are standard and taken from systemd-boot loader.conf.
    attributes = (
        EFI_ATTR_NON_VOLATILE
        | EFI_ATTR_RUNTIME
        | EFI_ATTR_BOOTSERVICE
        | EFI_ATTR_TIME_BASED_AUTH_WRITE
    )

    for variable, ns_guid, auth_file in (
        ("db", EFI_NS_SECURITY, db_auth),
        ("KEK", EFI_NS_GLOBAL, kek_auth),
        ("PK", EFI_NS_GLOBAL, pk_auth),  # Enrolling a PK exits Setup Mode, so this goes last.
    ):
        _write_efi_bytes(variable, ns_guid, attributes, auth_file.read_bytes())


def update_systemd_boot() -> None:
    """Updates systemd-boot in the ESP to the version shipped with secureblue. Invalidates PCR."""

    new_systemd = hashlib.file_digest(SYSTEMD_BOOT_NEW.open("rb"), "sha256").hexdigest()
    esp_boot = hashlib.file_digest(BOOTLOADER_ESP_BOOT.open("rb"), "sha256").hexdigest()
    esp_systemd = hashlib.file_digest(BOOTLOADER_ESP_SYSTEMD.open("rb"), "sha256").hexdigest()
    if new_systemd != esp_systemd:
        shutil.copy(SYSTEMD_BOOT_NEW, BOOTLOADER_ESP_SYSTEMD)
        # If BOOTX64.EFI is not a copy of systemd-bootx64.efi (e.g. dual-booting)
        # then we don't want to overwrite it.
        if esp_boot == esp_systemd:
            shutil.copy(SYSTEMD_BOOT_NEW, BOOTLOADER_ESP_BOOT)


def _mok_auth_hash(list_data: bytes, password: str) -> bytes:
    """Returns the 32-byte verifier for MokAuth. See mokutil `generate_auth()`.

    Args:
        list_data: The EFI_SIGNATURE_LIST being enrolled.
        password: Password the user must enter at the MOK screen to confirm enrollment.

    Returns:
        The SHA256 digest of `list_data` followed by the password.
    """
    digest = hashlib.sha256()
    digest.update(list_data)
    digest.update(password.encode("utf-16-le"))
    return digest.digest()


def enroll_mok_key(der: Path, *, password: str) -> None:
    """Stage a DER certificate for MOK enrollment on next boot.

    Args:
        der: Path to the DER-encoded certificate file.
        password: Password the user must enter at the MOK screen to confirm enrollment.
    """
    der_bytes = der.read_bytes()

    # MokNew takes an EFI_SIGNATURE_LIST. See EDK2 source:
    #
    # typedef struct {
    #   EFI_GUID    SignatureType;
    #   UINT32      SignatureListSize;
    #   UINT32      SignatureHeaderSize;
    #   UINT32      SignatureSize;
    #   /// UINT8           SignatureHeader[SignatureHeaderSize];
    #   /// EFI_SIGNATURE_DATA Signatures[][SignatureSize];
    # } EFI_SIGNATURE_LIST;
    #
    # typedef struct {
    #   EFI_GUID    SignatureOwner;
    #   UINT8       SignatureData[1];
    # } EFI_SIGNATURE_DATA;

    signature_type = uuid.UUID(EFI_TYPE_X509).bytes_le
    signature_size = EFI_GUID_SIZE + len(der_bytes)
    signature_list_size = EFI_GUID_SIZE + (EFI_UINT32_SIZE * 3) + signature_size
    signature_header_size = 0

    # We don't need a SignatureOwner for MOK.
    signature_owner = b"\x00" * EFI_GUID_SIZE

    mok_new_payload = (
        signature_type
        + struct.pack("<III", signature_list_size, signature_header_size, signature_size)
        + signature_owner
        + der_bytes
    )

    attrs = EFI_ATTR_NON_VOLATILE | EFI_ATTR_BOOTSERVICE | EFI_ATTR_RUNTIME
    mok_auth_payload = _mok_auth_hash(mok_new_payload, password)

    _write_efi_bytes("MokNew", EFI_NS_SHIM, attrs, mok_new_payload)
    _write_efi_bytes("MokAuth", EFI_NS_SHIM, attrs, mok_auth_payload)

    # To avoid boot failures if there's been a key rotation, we make sure
    # systemd-boot is up to date with any new signature or version.
    update_systemd_boot()


def main() -> int:
    """Execute the requested function."""

    request = deserialize(sys.stdin.read())

    match request:
        case EnrollEfiKeys():
            enroll_efi_keys(
                db_auth=Path(request.db_auth),
                kek_auth=Path(request.kek_auth),
                pk_auth=Path(request.pk_auth),
            )
            return 0
        case EnrollMokKey():
            enroll_mok_key(der=Path(request.der), password=request.password)
            return 0
        case _:
            print(f"Unhandled action: {request}", file=sys.stderr)
            return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
