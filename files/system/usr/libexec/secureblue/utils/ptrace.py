#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Utility functions involving ptrace
"""

from enum import StrEnum
from typing import Final

from . import get_selinux_booleans

SEBOOL_DENY_PTRACE: Final[str] = "deny_ptrace"
SEBOOL_CONTAINER_ALLOW_PTRACE: Final[str] = "container_allow_ptrace"
YAMA_DOC_URL: Final[str] = "https://www.kernel.org/doc/html/latest/admin-guide/LSM/Yama.html"


class PtraceStatus(StrEnum):
    """Representation of status of ptrace access on system"""

    DISABLED = "disabled"
    ADMIN_ONLY = "admin-only"
    CONTAINER_ONLY = "container-only"
    RESTRICTED = "restricted"
    UNRESTRICTED = "unrestricted"


def get_ptrace_status() -> PtraceStatus:
    """Get current ptrace status on system."""
    with open("/proc/sys/kernel/yama/ptrace_scope", encoding="utf-8") as f:
        ptrace_scope = int(f.read())
    sebools = get_selinux_booleans(SEBOOL_DENY_PTRACE, SEBOOL_CONTAINER_ALLOW_PTRACE)
    ptrace_denied = SEBOOL_DENY_PTRACE in sebools
    container_ptrace_allowed = SEBOOL_CONTAINER_ALLOW_PTRACE in sebools
    match (ptrace_scope, ptrace_denied, container_ptrace_allowed):
        case (0, _, _):
            status = PtraceStatus.UNRESTRICTED
        case (_, True, False) | (3, _, _):
            status = PtraceStatus.DISABLED
        case (2, False, _):
            status = PtraceStatus.ADMIN_ONLY
        case (1, False, _):
            status = PtraceStatus.RESTRICTED
        case (_, True, True):
            status = PtraceStatus.CONTAINER_ONLY
        case _ if ptrace_scope not in (0, 1, 2, 3):
            raise ValueError(f"invalid value '{ptrace_scope}' for ptrace_scope")
        case _:
            raise RuntimeError("unreachable")
    return status
