#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Remove hardened kernel arguments."""

# https://docs.kernel.org/admin-guide/kernel-parameters.html

from kargs_hardening_common import (
    DEFAULT_KARGS,
    DISABLE_32_BIT,
    FORCE_NOSMT,
    UNSTABLE_KARGS,
    apply_kargs,
)


def main() -> None:
    """Main script entry point."""
    kargs_to_remove = [*DEFAULT_KARGS, DISABLE_32_BIT, FORCE_NOSMT, *UNSTABLE_KARGS]

    print("Applying boot parameters...")
    apply_kargs(add=[], remove=kargs_to_remove)
    print("Hardening kernel arguments removed.")


if __name__ == "__main__":
    main()
