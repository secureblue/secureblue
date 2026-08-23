#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Common data for kernel argument hardening."""

import dataclasses
import json
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING

import sandbox
from utils import BootcBackend

from shared.secure_boot import Bootloader

if TYPE_CHECKING:
    from collections.abc import Sequence

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


@dataclass
class SetKargs:
    add: list[str]
    remove: list[str]


def serialize(request: SetKargs) -> str:
    """Serialises a data object to be passed to the inner function."""

    return json.dumps(dataclasses.asdict(request))


def deserialize(request: str) -> SetKargs:
    """Deserialises a data object passed to the inner function.

    Raises:
        TypeError: Unexpected fields for action.
    """

    data = json.loads(request)

    # TypeError if there are unexpected or missing fields.
    return SetKargs(**data)


def apply_kargs(*, add: Sequence[str], remove: Sequence[str]) -> None:
    """Add and remove kernel arguments. Ignores remove kargs if not set."""
    bootc_backend = BootcBackend.from_running()
    bootloader = Bootloader.from_running()

    if bootc_backend == BootcBackend.COMPOSEFS and bootloader == Bootloader.SYSTEMD_BOOT:
        worker = sandbox.SandboxedFunction(
            "set_kargs_uki.py",
            read_write_paths=["/boot/loader/addons/"],
        )

        request = SetKargs(list(add), list(remove))
        exit_code = worker.run(stdin=serialize(request))

        if exit_code:
            print(f"Worker failed (exit {exit_code})", file=sys.stderr)

        sys.exit(exit_code)

    elif bootc_backend == BootcBackend.OSTREE and bootloader == Bootloader.GRUB2:
        rpm_ostree_cmd = ["/usr/bin/rpm-ostree", "kargs"]
        for karg in add:
            rpm_ostree_cmd.append(f"--append-if-missing={karg}")
        for karg in remove:
            rpm_ostree_cmd.append(f"--delete-if-present={karg}")
        subprocess.run(rpm_ostree_cmd, check=True)

    else:
        print(f"Unexpected bootc backend and bootloader combination: {bootc_backend}, {bootloader}")
        sys.exit(1)
