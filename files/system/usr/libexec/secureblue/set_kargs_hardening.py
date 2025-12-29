#!/usr/bin/python3

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Add additional kernel arguments for hardening."""

# https://docs.kernel.org/admin-guide/kernel-parameters.html

from typing import Final

from kargs_hardening_common import (
    DEFAULT_KARGS,
    OPTIONAL_DISABLE_32BIT,
    OPTIONAL_FORCE_NOSMT,
    OPTIONAL_LOCKDOWN,
    UNSTABLE_KARGS,
    apply_kargs,
)
from utils import ImageModules, SecurebootStatus, ask_yes_no


def build_kargs_list(
    *, disable_32_bit: bool, nosmt: bool, unstable: bool, lockdown: bool
) -> tuple[list[str], list[str]]:
    """Build the list of kargs to add and remove."""
    kargs_to_add = DEFAULT_KARGS
    kargs_to_remove = []

    if disable_32_bit:
        kargs_to_add.append(OPTIONAL_DISABLE_32BIT)
    else:
        kargs_to_remove.append(OPTIONAL_DISABLE_32BIT)

    if nosmt:
        kargs_to_add.append(OPTIONAL_FORCE_NOSMT)
    else:
        kargs_to_remove.append(OPTIONAL_FORCE_NOSMT)

    if unstable:
        kargs_to_add += UNSTABLE_KARGS
    else:
        kargs_to_remove += UNSTABLE_KARGS

    if lockdown:
        kargs_to_add.append(OPTIONAL_LOCKDOWN)
    else:
        kargs_to_remove.append(OPTIONAL_LOCKDOWN)

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

QUESTION_LOCKDOWN: Final[str] = """
Would you like to enable kernel lockdown?
(Warning: Secure Boot is not enabled on your device. This means secureblue
modules such as Nvidia or ZFS will not work in lockdown mode.)
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

    # On systems without secure boot, kernel lockdown prevents some modules from loading.
    sb_enabled = SecurebootStatus.from_system() == SecurebootStatus.ENABLED
    sb_required = ImageModules.from_system().requires_secureboot()
    lockdown = True if sb_enabled or not sb_required else ask_yes_no(QUESTION_LOCKDOWN)

    kargs_to_add, kargs_to_remove = build_kargs_list(
        disable_32_bit=disable_32_bit,
        nosmt=nosmt,
        unstable=unstable,
        lockdown=lockdown,
    )

    print("\nApplying boot parameters...")
    apply_kargs(add=kargs_to_add, remove=kargs_to_remove)
    print("Hardening kernel arguments applied.")


if __name__ == "__main__":
    main()
