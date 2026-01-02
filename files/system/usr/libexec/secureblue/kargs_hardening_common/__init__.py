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

"""Common data for kernel argument hardening."""

import subprocess  # nosec
from collections.abc import Iterable, Sequence

import tomllib

with open("/usr/lib/bootc/kargs.d/10-secureblue.toml", "rb") as f:
    DEFAULT_KARGS = tomllib.load(f)["kargs"]

try:
    with open("/usr/lib/bootc/kargs.d/20-nvidia.toml", "rb") as f:
        IMAGE_NVIDIA_KARGS = tomllib.load(f)["kargs"]
except FileNotFoundError:
    IMAGE_NVIDIA_KARGS = None

OPTIONAL_DISABLE_32BIT = "ia32_emulation=0"
OPTIONAL_FORCE_NOSMT = "nosmt=force"
OPTIONAL_LOCKDOWN = "lockdown=confidentiality"

UNSTABLE_KARGS = [
    "amd_iommu=force_isolation",
    "bdev_allow_write_mounted=0",
    "debugfs=off",
    "efi=disable_early_pci_dma",
    "gather_data_sampling=force",
    "mem_encrypt=on",
    "oops=panic",
]

KNOWN_EXACT_KARGS = (
    DEFAULT_KARGS
    + UNSTABLE_KARGS
    + (IMAGE_NVIDIA_KARGS if IMAGE_NVIDIA_KARGS is not None else [])
    + [
        "quiet",
        "rhgb",
        "rw",
        OPTIONAL_DISABLE_32BIT,
        OPTIONAL_FORCE_NOSMT,
        OPTIONAL_LOCKDOWN,
    ]
)

KNOWN_PREFIX_KARGS = [
    "module.sig_enforce=",
    "ostree=",
    "preempt=",
    "rd.luks.uuid=",
    "root=",
    "rootflags=",
    "vconsole.keymap=",
]


def apply_kargs(*, add: Sequence[str], remove: Sequence[str]) -> None:
    """Add and remove kernel arguments."""
    rpm_ostree_cmd = ["/usr/bin/rpm-ostree", "kargs"]
    for karg in add:
        rpm_ostree_cmd.append(f"--append-if-missing={karg}")
    for karg in remove:
        rpm_ostree_cmd.append(f"--delete-if-present={karg}")
    subprocess.run(rpm_ostree_cmd, check=True)  # nosec


def get_unknown_kargs(kargs: Iterable[str]) -> list[str]:
    """Get kernel arguments not set or otherwise expected by secureblue."""
    return [
        karg
        for karg in kargs
        if karg not in KNOWN_EXACT_KARGS
        and not any(karg.startswith(prefix) for prefix in KNOWN_PREFIX_KARGS)
    ]
