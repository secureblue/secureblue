#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Add additional kernel arguments for hardening."""

# https://docs.kernel.org/admin-guide/kernel-parameters.html

from typing import Final

from shared.kargs_hardening import (
    DEFAULT_KARGS,
    DISABLE_32_BIT,
    FORCE_NOSMT,
    UNSTABLE_KARGS,
    apply_kargs,
)
from shared.secure_boot import Bootloader
from utils import BootcBackend, ask_yes_no


def build_kargs_list(
    *, disable_32_bit: bool, nosmt: bool, unstable: bool
) -> tuple[list[str], list[str]]:
    """Build the list of kargs to add and remove."""
    kargs_to_add = []
    kargs_to_remove = []

    if (
        BootcBackend.from_running() == BootcBackend.OSTREE
        and Bootloader.from_running() == Bootloader.GRUB2
    ):
        kargs_to_add += DEFAULT_KARGS

    if disable_32_bit:
        kargs_to_add.append(DISABLE_32_BIT)
    else:
        kargs_to_remove.append(DISABLE_32_BIT)

    if nosmt:
        kargs_to_add.append(FORCE_NOSMT)
    else:
        kargs_to_remove.append(FORCE_NOSMT)

    if unstable:
        kargs_to_add += UNSTABLE_KARGS
    else:
        kargs_to_remove += UNSTABLE_KARGS

    return kargs_to_add, kargs_to_remove


QUESTION_32_BIT: Final[str] = """
Do you need support for 32-bit processes/syscalls? (This is mostly used by
legacy software, with some exceptions, such as Steam.)
"""

QUESTION_NOSMT: Final[str] = """
Do you want to force disable Simultaneous Multithreading (SMT) / Hyperthreading?
(This can cause a reduction in the performance of certain tasks in favor of
security. Note that in most hardware SMT will be disabled anyways to mitigate
a known vulnerability; this turns it off on all hardware regardless.)
"""

QUESTION_UNSTABLE: Final[str] = """
Would you like to set additional (unstable) hardening kernel arguments?
(Warning: Setting these kernel arguments may lead to boot or stability issues
on some hardware.)
"""


def main() -> None:
    """Main entry point for script."""
    disable_32_bit = not ask_yes_no(QUESTION_32_BIT)
    if disable_32_bit:
        print("Selected: disable 32-bit support.")
    else:
        print("Selected: keep 32-bit support.")

    nosmt = ask_yes_no(QUESTION_NOSMT)
    if nosmt:
        print("Selected: force disable SMT/hyperthreading.")
    else:
        print("Selected: do not force disable SMT/hyperthreading.")

    unstable = ask_yes_no(QUESTION_UNSTABLE)
    if unstable:
        print("Selected: set unstable hardening kernel arguments.")
    else:
        print("Selected: do not set unstable hardening kernel arguments.")

    kargs_to_add, kargs_to_remove = build_kargs_list(
        disable_32_bit=disable_32_bit,
        nosmt=nosmt,
        unstable=unstable,
    )

    print("\nApplying boot parameters...")
    apply_kargs(add=kargs_to_add, remove=kargs_to_remove)
    print("Hardening kernel arguments applied.")


if __name__ == "__main__":
    main()
