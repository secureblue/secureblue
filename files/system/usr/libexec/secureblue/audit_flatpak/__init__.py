#!/usr/bin/python3

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""
Flatpak permissions checks for secureblue auditing script.
"""

from dataclasses import dataclass, field
from typing import Final

from auditor import Status

PASS: Final = Status.PASS
INFO: Final = Status.INFO
WARN: Final = Status.WARN
FAIL: Final = Status.FAIL


@dataclass
class Permissions:
    """Object representing permissions for a flatpak app."""

    permissions: dict[str, list[str]] = field(default_factory=dict)
    environment: dict[str, str] = field(default_factory=dict)
    session_bus_talk: list[str] = field(default_factory=list)
    session_bus_own: list[str] = field(default_factory=list)
    system_bus_talk: list[str] = field(default_factory=list)
    system_bus_own: list[str] = field(default_factory=list)


def parse_flatpak_permissions(perms_text: str) -> Permissions:
    """Get permissions for an installed flatpak."""
    perms = Permissions()
    section = None
    for line in perms_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            section = line.strip("[]")
            continue
        key, value = line.split("=", maxsplit=1)
        match section:
            case "Session Bus Policy":
                match value:
                    case "talk":
                        perms.session_bus_talk.append(key)
                    case "own":
                        perms.session_bus_own.append(key)
                    case _:
                        raise ValueError(f"Unknown session bus permission '{value}'")
            case "System Bus Policy":
                match value:
                    case "talk":
                        perms.system_bus_talk.append(key)
                    case "own":
                        perms.system_bus_own.append(key)
                    case _:
                        raise ValueError(f"Unknown system bus permission '{value}'")
            case "Environment":
                perms.environment[key] = value
            case _:
                perms.permissions[key] = [val for val in value.split(";") if val]
    return perms


ALIASES: dict[str, str] = {
    "xdg-cache": "~/.cache",
    "xdg-config": "~/.config",
    "xdg-data": "~/.local/share",
    "xdg-desktop": "~/Desktop",
    "xdg-documents": "~/Documents",
    "xdg-downloads": "~/Downloads",
    "xdg-music": "~/Music",
    "xdg-pictures": "~/Pictures",
    "xdg-public-share": "~/Public",
    "xdg-templates": "~/Templates",
    "xdg-videos": "~/Videos",
    "home": "~",  # "~" must be the last entry in the dict
}


def parse_fs_permission(perm: str) -> tuple[str, bool, bool, bool]:
    """Parse flatpak filesystem permission string."""
    readonly = perm.endswith(":ro")
    negated = perm.startswith("!")
    if perm.endswith(":ro"):
        path = perm.removesuffix(":ro")
    elif perm.endswith(":rw"):
        path = perm.removesuffix(":rw")
    elif perm.endswith(":create"):
        path = perm.removesuffix(":create")
    else:
        path = perm
    path = path.removeprefix("!").rstrip("/")
    is_alias = False
    for name, alias in ALIASES.items():
        if path.startswith(alias):
            path = path.replace(alias, name, count=1)
            is_alias = True
            break
    return path, readonly, negated, is_alias


FLATPAK_OVERRIDE_OPTIONS: dict[str, tuple[str, str]] = {
    "shared": ("share", "unshare"),
    "sockets": ("socket", "nosocket"),
    "devices": ("device", "nodevice"),
    "features": ("allow", "disallow"),
}


@dataclass(frozen=True)
class PermissionCheck:
    """A flatpak permission to be checked, and how it's reported if present."""

    category: str
    permission: str
    status: Status
    description: str | None = None
    note: str | None = None
    endnote: str | None = None
    sandbox_escape: bool = False
    arbitrary_permissions: bool = False

    def warning(self, name: str) -> str:
        """Give the warning text for if the check fails."""
        perm_type = FLATPAK_OVERRIDE_OPTIONS[self.category][0]
        description = self.description or f"has {perm_type}={self.permission}"
        return f"{name} {description}"

    def recommendation(self, name: str) -> str:
        """Give the recommendation text for if the check fails."""
        if self.sandbox_escape:
            sandbox_escape_note = "This may also be used as a sandbox escape vector."
        else:
            sandbox_escape_note = ""
        option = FLATPAK_OVERRIDE_OPTIONS[self.category][1]
        rec = f"""{self.warning(name)}.
            {self.note or ""}
            {sandbox_escape_note}
            To remove this permission, use Flatseal or run:
            $ flatpak override -u --{option}={self.permission} {name}
            {self.endnote or ""}"""
        return "\n".join(line.strip() for line in rec.split("\n") if line.strip())


FLATPAK_PERMISSION_CHECKS: list[PermissionCheck] = [
    PermissionCheck("shared", "network", INFO, "has network access"),
    PermissionCheck("shared", "ipc", INFO, "has inter-process communications access"),
    PermissionCheck("sockets", "x11", FAIL, "has X11 access"),
    PermissionCheck("sockets", "pulseaudio", WARN, "has access to the PulseAudio socket"),
    PermissionCheck(
        "sockets",
        "session-bus",
        FAIL,
        "has access to the D-Bus session bus",
        note="This grants access to audio and microphones.",
    ),
    PermissionCheck("sockets", "system-bus", FAIL, "has access to the D-Bus system bus"),
    PermissionCheck("sockets", "ssh-auth", WARN, "has access to the SSH agent"),
    PermissionCheck(
        "devices",
        "all",
        FAIL,
        note="This grants access to input devices, GPUs, raw USB, and virtualization.",
        sandbox_escape=True,
        endnote="If GPU access is required, allow device=dri instead.",
    ),
    PermissionCheck("devices", "input", INFO, note="This grants access to input devices."),
    PermissionCheck(
        "devices", "kvm", WARN, note="This grants access to kernel-based virtualization."
    ),
    PermissionCheck(
        "devices", "shm", FAIL, note="This grants access to shared memory.", sandbox_escape=True
    ),
    PermissionCheck(
        "devices", "usb", WARN, note="This grants raw USB device access.", sandbox_escape=True
    ),
    PermissionCheck("features", "bluetooth", WARN, "has bluetooth access"),
    PermissionCheck("features", "devel", WARN, "has ptrace access"),
]


def check_flatpak_permissions(
    name: str, perms: Permissions, bluetooth_loaded: bool, ptrace_allowed: bool
) -> tuple[Status, list[str], list[str]]:
    """Check permissions for a single flatpak."""
    warnings = []
    recs = []
    status = PASS
    arbitrary_permissions = False

    for check in FLATPAK_PERMISSION_CHECKS:
        if check.category not in perms.permissions:
            continue
        if check.permission in perms.permissions[check.category]:
            if check.category == "features":
                if check.permission == "bluetooth" and not bluetooth_loaded:
                    continue
                if check.permission == "devel" and not ptrace_allowed:
                    continue
            status = status.downgrade_to(check.status)
            warnings.append(check.warning(name))
            recs.append(check.recommendation(name))
            if check.arbitrary_permissions:
                arbitrary_permissions = True

    filesystems = perms.permissions.get("filesystems")
    filesystems_ro = {}
    filesystems_rw = {}
    if filesystems is not None:
        for perm in filesystems:
            path, readonly, negated, is_alias = parse_fs_permission(perm)
            if negated:
                continue
            if readonly:
                filesystems_ro[path] = is_alias
            else:
                filesystems_rw[path] = is_alias

        dangerous_dirs = {
            "host": {
                "status": FAIL,
                "access": "all system files",
            },
            "home": {
                "status": FAIL,
                "access": "all user files",
            },
            "xdg-config": {
                "status": FAIL,
                "access": "other applications' configuration files",
            },
            "xdg-cache": {
                "status": FAIL,
                "access": "other applications' cache files",
            },
            "xdg-data": {
                "status": FAIL,
                "access": "other applications' data files",
            },
        }
        for path, dir_data in dangerous_dirs.items():
            if path in filesystems_rw:
                status = status.downgrade_to(dir_data["status"])
                is_alias = filesystems_rw[path]
                if is_alias:
                    path = path.replace(path, ALIASES[path], count=1)
                warnings.append(f"{name} has filesystem={path} permission")
                recs.append(
                    f"""{name} has filesystem={path} permission.
                        This grants access to {dir_data["access"]}.
                        To remove this permission, use Flatseal or run:
                        $ flatpak override -u --nofilesystem={path} {name}"""
                )

        override_path = "xdg-data/flatpak/overrides"
        if override_path in filesystems_rw:
            arbitrary_permissions = True
            is_alias = filesystems_rw[override_path]
            if is_alias:
                override_path = override_path.replace("xdg-data", ALIASES["xdg-data"], count=1)
            recs.append(
                f"""{name} can modify flatpak overrides.
                    This grants the ability to acquire arbitrary permissions.
                    To remove this permission, use Flatseal or run:
                    $ flatpak override -u --nofilesystem={override_path} {name}"""
            )

    if filesystems is None or ("host-os" not in filesystems_ro and "host-os" not in filesystems_rw):
        status = status.downgrade_to(WARN)
        warnings.append(f"{name} is missing host-os:ro permission")
        recs.append(
            f"""{name} is missing host-os:ro permission.
                This is required to load hardened_malloc.
                To add this permission, use Flatseal or run:
                $ flatpak override -u --filesystem=host-os:ro {name}"""
        )

    for bus_name in ("org.freedesktop.Flatpak", "org.freedesktop.impl.portal.PermissionStore"):
        if bus_name in perms.session_bus_talk:
            arbitrary_permissions = True
            recs.append(
                f"""{name} can talk to {bus_name} on the session bus.
                    This grants the ability to acquire arbitrary permissions.
                    To remove this permission, use Flatseal or run:
                    $ flatpak override -u --no-talk-name={bus_name} {name}"""
            )

    ld_preload = perms.environment.get("LD_PRELOAD")
    if ld_preload is None:
        ld_preload_files = []
    else:
        ld_preload_files = [s.rsplit("/", maxsplit=1)[-1] for s in ld_preload.split()]
    if "libhardened_malloc.so" not in ld_preload_files:
        warnings.append(f"{name} is not requesting hardened_malloc")
        if "libhardened_malloc-light.so" in ld_preload_files:
            status = status.downgrade_to(INFO)
            warnings.append(f"{name} is requesting hardened_malloc-light")
        elif "libhardened_malloc-pkey.so" in ld_preload_files:
            status = status.downgrade_to(INFO)
            warnings.append(f"{name} is requesting hardened_malloc-pkey")
        else:
            status = status.downgrade_to(WARN)
        recs.append(
            f"""{name} is not requesting hardened_malloc.
                To enable it, run:
                $ ujust harden-flatpak {name}"""
        )

    if arbitrary_permissions:
        status = status.downgrade_to(FAIL)
        warnings.append(f"{name} can acquire arbitrary permissions")

    return status, warnings, recs
