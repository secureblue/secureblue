#!/usr/bin/python3

"""Shared data objects for `ujust enroll-secure-boot-keys`."""

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import enum
import json
import struct
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

EFIVARS = Path("/sys/firmware/efi/efivars")

# UEFI variable namespaces. These are mostly relevant as the predictable suffix
# after an efivar, like /sys/firmware/efi/efivars/{VARIABLE}-{NAMESPACE_GUID}.
# See S3.3: <https://uefi.org/sites/default/files/resources/UEFI_Spec_2_10_Aug29.pdf>
EFI_NS_GLOBAL = "8be4df61-93ca-11d2-aa0d-00e098032b8c"  # EFI_GLOBAL_VARIABLE
EFI_NS_SECURITY = "d719b2cb-3d3a-4596-a3bc-dad00e67656f"  # EFI_IMAGE_SECURITY_DATABASE_GUID
# https://github.com/rhboot/shim/blob/c17fdb2ff23c9e28615782ac9ae268ed6a8f71f4/lib/guid.c
EFI_NS_SHIM = "605dab50-e046-4300-abb6-3dd810dd8b23"  # SHIM_LOCK_GUID
EFI_NS_SYSTEMD = "4a67b082-0a4c-41cf-b6c7-440b29bb8c4f"  # systemd vendor GUID

# UEFI types.
EFI_TYPE_X509 = "a5c059a1-94e4-4aa7-87b5-ab155c2bf072"  # EFI_CERT_X509_GUID

# UEFI binary layout sizes (bytes).
EFI_UINT32_SIZE = 4
EFI_GUID_SIZE = 16


@dataclass
class EnrollEfiKeys:
    """Shared data object for calling `enroll_efi_keys(db_auth, kek_auth, pk_auth)`."""

    action: Literal["enroll_efi_keys"] = "enroll_efi_keys"
    db_auth: str = ""
    kek_auth: str = ""
    pk_auth: str = ""


@dataclass
class EnrollMokKey:
    """Shared data object for calling `enroll_mok_key(der, password)`."""

    action: Literal["enroll_mok_key"] = "enroll_mok_key"
    der: str = ""
    password: str = ""


_TYPES: dict[str, type] = {
    "enroll_efi_keys": EnrollEfiKeys,
    "enroll_mok_key": EnrollMokKey,
}


def read_efivar(name: str, ns_guid: str) -> bytes:
    """Returns the raw contents of a UEFI variable."""

    path = EFIVARS / f"{name}-{ns_guid}"
    data = path.read_bytes()

    # Strip the attributes uint to get the data.
    return data[EFI_UINT32_SIZE:]


def read_efivar_str(name: str, ns_guid: str) -> str:
    """Returns the string contents of a UEFI variable."""
    return read_efivar(name, ns_guid).decode("utf-16-le").rstrip("\x00")


def is_cert_in_signature_list(der: Path, efivar: Path) -> bool:
    """Return whether the DER certificate is present in the given EFI_SIGNATURE_LIST.

    Raises:
        FileNotFoundError: Either the certificate or efivar could not be found.
    """

    der_bytes = der.read_bytes()
    sig_list = efivar.read_bytes()[EFI_UINT32_SIZE:]  # Strip attributes.
    x509_guid = uuid.UUID(EFI_TYPE_X509).bytes_le

    # See EDK2 source:
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

    sig_list_header_size = EFI_GUID_SIZE + (EFI_UINT32_SIZE * 3)
    list_offset = 0

    while list_offset + sig_list_header_size <= len(sig_list):
        sig_type = sig_list[list_offset : list_offset + EFI_GUID_SIZE]
        sig_list_size, sig_header_size, sig_size = struct.unpack_from(
            "<III", sig_list, list_offset + EFI_GUID_SIZE
        )

        if sig_list_size == 0:
            break

        if sig_type == x509_guid and sig_size > EFI_GUID_SIZE:
            entries_start = list_offset + sig_list_header_size + sig_header_size
            entries_end = list_offset + sig_list_size

            for entry_offset in range(entries_start, entries_end, sig_size):
                # EFI_SIGNATURE_DATA is owner GUID, then the certificate.
                cert = sig_list[entry_offset + EFI_GUID_SIZE : entry_offset + sig_size]
                if cert == der_bytes:
                    return True

        list_offset += sig_list_size

    return False


def is_secure_boot_enabled() -> bool:
    """Returns whether Secure Boot is enabled."""
    return read_efivar("SecureBoot", EFI_NS_GLOBAL)[0] == 1


def is_setup_mode_enabled() -> bool:
    """Returns whether the system is in Setup Mode."""
    return read_efivar("SetupMode", EFI_NS_GLOBAL)[0] == 1


class Bootloader(enum.Enum):
    """A bootloader, e.g. `GRUB2` or `SYSTEMD_BOOT`."""

    SYSTEMD_BOOT = enum.auto()
    GRUB2 = enum.auto()

    @classmethod
    def from_running(cls) -> "Bootloader":
        """Gets the `Bootloader` in use on the running system.

        Raises:
            RuntimeError: The bootloader could not be determined.
            FileNotFoundError: Could not find systemd `LoaderInfo` efivar.
        """

        raw_bootloader = read_efivar_str("LoaderInfo", EFI_NS_SYSTEMD)
        if "GRUB 2" in raw_bootloader:
            return cls.GRUB2
        if "systemd-boot" in raw_bootloader:
            return cls.SYSTEMD_BOOT
        raise RuntimeError(f"Unknown bootloader: {raw_bootloader}")


def is_shim_system() -> bool:
    """Returns whether the system booted with shim."""
    return (EFIVARS / f"MokListRT-{EFI_NS_SHIM}").exists()


def is_efi_system() -> bool:
    """Returns whether the system has a UEFI firmware."""
    return EFIVARS.exists()


def serialize(request: EnrollEfiKeys | EnrollMokKey) -> str:
    """Serialises a data object to be passed to the inner function."""

    return json.dumps(dataclasses.asdict(request))


def deserialize(request: str) -> EnrollEfiKeys | EnrollMokKey:
    """Deserialises a data object passed to the inner function.

    Raises:
        ValueError: Unknown action type.
        TypeError: Unexpected fields for action.
    """

    data = json.loads(request)
    action = data.get("action")
    cls = _TYPES.get(action)
    if cls is None:
        raise ValueError(f"Unknown action for secure boot worker: {action!r}")

    # TypeError if there are unexpected or missing fields.
    return cls(**data)
