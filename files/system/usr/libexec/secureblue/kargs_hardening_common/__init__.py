#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Common data for kernel argument hardening."""

import subprocess  # nosec
from collections.abc import Sequence

import tomllib

with open("/usr/lib/bootc/kargs.d/10-secureblue.toml", "rb") as f:
    DEFAULT_KARGS = tomllib.load(f)["kargs"]

try:
    with open("/usr/lib/bootc/kargs.d/20-nvidia.toml", "rb") as f:
        IMAGE_NVIDIA_KARGS = tomllib.load(f)["kargs"]
except FileNotFoundError:
    IMAGE_NVIDIA_KARGS = None

DISABLE_32_BIT = "ia32_emulation=0"

FORCE_NOSMT = "nosmt=force"

UNSTABLE_KARGS = [
    "amd_iommu=force_isolation",
    "bdev_allow_write_mounted=0",
    "debugfs=off",
    "efi=disable_early_pci_dma",
    "gather_data_sampling=force",
    "mem_encrypt=on",
    "oops=panic",
]

MODULE_SIG_ENFORCE = "module.sig_enforce=1"
MODULE_NO_SIG_ENFORCE = "module.sig_enforce=0"


def apply_kargs(*, add: Sequence[str], remove: Sequence[str]) -> None:
    """Add and remove kernel arguments."""
    rpm_ostree_cmd = ["/usr/bin/rpm-ostree", "kargs"]
    for karg in add:
        rpm_ostree_cmd.append(f"--append-if-missing={karg}")
    for karg in remove:
        rpm_ostree_cmd.append(f"--delete-if-present={karg}")
    subprocess.run(rpm_ostree_cmd, check=True)  # nosec
