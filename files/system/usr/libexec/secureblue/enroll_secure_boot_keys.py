#!/usr/bin/python3

"""Enrolls secure boot keys into shim or the firmware - `ujust enroll-secure-boot-keys`."""

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import sys
from pathlib import Path

import sandbox
from shared.secure_boot import (
    EFI_NS_GLOBAL,
    EFI_NS_SHIM,
    EFIVARS,
    Bootloader,
    EnrollEfiKeys,
    EnrollMokKey,
    is_cert_in_signature_list,
    is_efi_system,
    is_secure_boot_enabled,
    is_setup_mode_enabled,
    is_shim_system,
    serialize,
)

AKMODS_DER_PATH = "/usr/share/pki/akmods/certs/akmods-secureblue.der"
DB_AUTH_PATH = "/usr/share/secureblue/uki/keys/db.auth"
DB_DER_PATH = "/usr/share/secureblue/uki/keys/db.der"
KEK_AUTH_PATH = "/usr/share/secureblue/uki/keys/KEK.auth"
PK_AUTH_PATH = "/usr/share/secureblue/uki/keys/PK.auth"
PK_DER_PATH = "/usr/share/secureblue/uki/keys/PK.der"

worker = sandbox.SandboxedFunction(
    "secure_boot.py", read_write_paths=[EFIVARS.as_posix()], capabilities=["CAP_LINUX_IMMUTABLE"]
)


def required_mok_cert() -> str:
    """Returns the MOK certificate that should be installed on the running system."""
    return AKMODS_DER_PATH if Bootloader.from_running() == Bootloader.GRUB2 else DB_DER_PATH


def is_mok_installed() -> bool:
    """Returns whether the secureblue MOK is installed."""
    return is_cert_in_signature_list(
        Path(required_mok_cert()), EFIVARS / f"MokListRT-{EFI_NS_SHIM}"
    )


def is_pk_installed() -> bool:
    """Returns whether the secureblue Platform Key is installed."""
    try:
        return is_cert_in_signature_list(Path(PK_DER_PATH), EFIVARS / f"PK-{EFI_NS_GLOBAL}")
    except FileNotFoundError:
        # Can be normal in Setup Mode.
        return False


def print_status(is_shim: bool) -> None:
    """Prints the Secure Boot key enrollment status."""

    if not is_efi_system():
        print("Status: unavailable")
        return

    key_installed = is_mok_installed() if is_shim else is_pk_installed()
    print("Status: enrolled" if key_installed else "Status: not enrolled")


def install_pk() -> int:
    """Installs the Platform Key. Returns error/success exit code."""

    if is_pk_installed():
        print("The secureblue Platform Key is already enrolled.")
        if not is_secure_boot_enabled():
            print("Secure Boot is not enabled. Please do this in `ujust bios`.")
        return 0

    if not is_setup_mode_enabled():
        print(
            "The firmware is not in Setup Mode.\n"
            "Please remove the existing Platform Key in `ujust bios`."
        )
        return 1

    request = EnrollEfiKeys(db_auth=DB_AUTH_PATH, kek_auth=KEK_AUTH_PATH, pk_auth=PK_AUTH_PATH)
    exit_code = worker.run(stdin=serialize(request))

    if exit_code:
        print(f"Worker failed (exit {exit_code})", file=sys.stderr)
        return exit_code

    if is_pk_installed():
        print("The secureblue Platform Key was successfully enrolled.")
        return 0

    print("Unable to install the secureblue Platform Key. Reboot and try again.")
    return 1


def install_mok() -> int:
    """Install the MOK. Returns error/success exit code."""

    if is_mok_installed():
        print("The secureblue MOK is already enrolled.")
        return 0

    if not is_secure_boot_enabled():
        print("Secure Boot is not enabled. Please do this in `ujust bios`.")

    request = EnrollMokKey(der=required_mok_cert(), password="secureblue")  # noqa: S106
    exit_code = worker.run(stdin=serialize(request))

    if exit_code:
        print(f"Worker failed (exit {exit_code})", file=sys.stderr)
        return exit_code

    print(
        "The secureblue MOK has been queued for enrollment.\n"
        "Please reboot and enter the password 'secureblue' when prompted."
    )
    return 0


def main() -> int:
    """Enroll MOK or Platform Key depending on bootc backend."""

    is_shim = is_shim_system()

    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print_status(is_shim)
        return 0

    # User wants to enroll a key.
    if not is_efi_system():
        print(
            "Secure Boot is not available on your system.\n"
            "If you have a dual-mode system, switch it from BIOS to UEFI mode and try again."
        )
        return 1

    # We're running on a UEFI system.
    if is_shim:
        return install_mok()

    return install_pk()


if __name__ == "__main__":
    sys.exit(main())
