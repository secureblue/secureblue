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
            path = path.replace(alias, name, 1)
            is_alias = True
            break
    return path, readonly, negated, is_alias


FLATPAK_OVERRIDE_OPTIONS: Final[dict[str, tuple[str, str]]] = {
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


@dataclass(frozen=True)
class DirectoryInfo:
    """Info about a directory to check."""

    path: str
    description: str
    status: Status


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
        "devices",
        "shm",
        FAIL,
        note="This grants access to shared memory.",
        sandbox_escape=True,
    ),
    PermissionCheck(
        "devices",
        "usb",
        WARN,
        note="This grants raw USB device access.",
        sandbox_escape=True,
    ),
    PermissionCheck("features", "bluetooth", WARN, "has bluetooth access"),
    PermissionCheck("features", "devel", WARN, "has ptrace access"),
]

ARBITRARY_PERMISSIONS_EXPECTED: list[str] = [
    "com.github.tchx84.Flatseal",
    "io.github.flattool.Warehouse",
]


@dataclass
class FlatpakPermissionsState:
    """The state of a flatpak's permissions."""

    warnings: list[str]
    recs: list[str]
    status: Status
    arbitrary_permissions: bool
    name: str


def check_flatpak_permissions(
    name: str, perms: Permissions, bluetooth_loaded: bool, ptrace_allowed: bool
) -> FlatpakPermissionsState:
    """Check permissions for a single flatpak."""
    flatpak_permissions_state = FlatpakPermissionsState([], [], PASS, False, name)

    _check_predefined_flatpak_permissions(
        flatpak_permissions_state, perms, bluetooth_loaded, ptrace_allowed
    )
    _check_fs_permissions(flatpak_permissions_state, perms)
    _handle_flatpak_buses(flatpak_permissions_state, perms)
    _check_ld_preload(flatpak_permissions_state, perms)
    _handle_arbitrary_permissions(flatpak_permissions_state)

    return flatpak_permissions_state


def _handle_arbitrary_permissions(state: FlatpakPermissionsState):
    if state.arbitrary_permissions:
        if state.name in ARBITRARY_PERMISSIONS_EXPECTED:
            state.status = state.status.downgrade_to(INFO)
            state.warnings.append(
                f"""{state.name} can acquire arbitrary permissions.
                However, this is required for its functionality."""
            )
        else:
            state.status = state.status.downgrade_to(FAIL)
            state.warnings.append(f"{state.name} can acquire arbitrary permissions")


def _check_ld_preload(state: FlatpakPermissionsState, perms: Permissions):
    ld_preload = perms.environment.get("LD_PRELOAD")
    if ld_preload is None:
        ld_preload_files = []
    else:
        ld_preload_files = [s.rsplit("/", maxsplit=1)[-1] for s in ld_preload.split()]
    if "libhardened_malloc.so" not in ld_preload_files:
        state.warnings.append(f"{state.name} is not requesting hardened_malloc")
        if "libhardened_malloc-light.so" in ld_preload_files:
            state.status = state.status.downgrade_to(INFO)
            state.warnings.append(f"{state.name} is requesting hardened_malloc-light")
        elif "libhardened_malloc-pkey.so" in ld_preload_files:
            state.status = state.status.downgrade_to(INFO)
            state.warnings.append(f"{state.name} is requesting hardened_malloc-pkey")
        else:
            state.status = state.status.downgrade_to(WARN)
        state.recs.append(
            f"""{state.name} is not requesting hardened_malloc.
                    To enable it, run:
                    $ ujust harden-flatpak {state.name}"""
        )


def _handle_flatpak_buses(state: FlatpakPermissionsState, perms: Permissions):
    for bus_name in ("org.freedesktop.Flatpak", "org.freedesktop.impl.portal.PermissionStore"):
        if bus_name in perms.session_bus_talk:
            state.arbitrary_permissions = True
            if state.name not in ARBITRARY_PERMISSIONS_EXPECTED:
                state.recs.append(
                    f"""{state.name} can talk to {bus_name} on the session bus.
                        This grants the ability to acquire arbitrary permissions.
                        To remove this permission, use Flatseal or run:
                        $ flatpak override -u --no-talk-name={bus_name} {state.name}"""
                )


def _predefined_check_applies(
    check: PermissionCheck,
    existing_permissions: Permissions,
    bluetooth_loaded: bool,
    ptrace_allowed: bool,
) -> bool:
    is_irrelevant_permission = check.category == "features" and (
        (check.permission == "bluetooth" and not bluetooth_loaded)
        or (check.permission == "devel" and not ptrace_allowed)
    )
    return (
        not is_irrelevant_permission
        and check.category in existing_permissions.permissions
        and check.permission in existing_permissions.permissions[check.category]
    )


def _check_predefined_flatpak_permissions(
    state: FlatpakPermissionsState,
    existing_permissions: Permissions,
    bluetooth_loaded: bool,
    ptrace_allowed: bool,
):
    for check in FLATPAK_PERMISSION_CHECKS:
        if _predefined_check_applies(check, existing_permissions, bluetooth_loaded, ptrace_allowed):
            state.status = state.status.downgrade_to(check.status)
            state.warnings.append(check.warning(state.name))
            state.recs.append(check.recommendation(state.name))
            state.arbitrary_permissions |= check.arbitrary_permissions


def _check_dangerous_dirs(state: FlatpakPermissionsState, filesystems_rw: dict[str, bool]):
    dangerous_dirs: list[DirectoryInfo] = [
        DirectoryInfo("host", "all system files", FAIL),
        DirectoryInfo("home", "all user files", FAIL),
        DirectoryInfo("xdg-config", "other applications' configuration files", FAIL),
        DirectoryInfo("xdg-cache", "other applications' cache files", FAIL),
        DirectoryInfo("xdg-data", "other applications' data files", FAIL),
    ]

    for directory in dangerous_dirs:
        if directory.path in filesystems_rw:
            aliased_path = directory.path
            state.status = state.status.downgrade_to(directory.status)
            is_alias = filesystems_rw[directory.path]
            if is_alias:
                aliased_path = directory.path.replace(directory.path, ALIASES[directory.path], 1)
            state.warnings.append(f"{state.name} has filesystem={directory.path} permission")
            state.recs.append(
                f"""{state.name} has filesystem={aliased_path} permission.
                        This grants access to {directory.description}.
                        To remove this permission, use Flatseal or run:
                        $ flatpak override -u --nofilesystem={aliased_path} {state.name}"""
            )


def _check_hardened_malloc_access(
    state: FlatpakPermissionsState,
    filesystems: list[str] | None,
    filesystems_rw: dict[str, bool],
    filesystems_ro: dict[str, bool],
):
    if filesystems is None or ("host-os" not in filesystems_ro and "host-os" not in filesystems_rw):
        state.status = state.status.downgrade_to(WARN)
        state.warnings.append(f"{state.name} is missing host-os:ro permission")
        state.recs.append(
            f"""{state.name} is missing host-os:ro permission.
                    This is required to load hardened_malloc.
                    To add this permission, use Flatseal or run:
                    $ flatpak override -u --filesystem=host-os:ro {state.name}"""
        )


def _check_overrides_access(state: FlatpakPermissionsState, filesystems_rw: dict[str, bool]):
    override_path = "xdg-data/flatpak/overrides"
    if override_path in filesystems_rw:
        state.arbitrary_permissions = True
        is_alias = filesystems_rw[override_path]
        if is_alias:
            override_path = override_path.replace("xdg-data", ALIASES["xdg-data"], 1)
        if state.name not in ARBITRARY_PERMISSIONS_EXPECTED:
            state.recs.append(
                f"""{state.name} can modify flatpak overrides.
                                This grants the ability to acquire arbitrary permissions.
                                To remove this permission, use Flatseal or run:
                                $ flatpak override -u --nofilesystem={override_path} {state.name}"""
            )


def _check_fs_permissions(state: FlatpakPermissionsState, perms: Permissions):
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
        _check_dangerous_dirs(state, filesystems_rw)
        _check_overrides_access(state, filesystems_rw)
    _check_hardened_malloc_access(state, filesystems, filesystems_rw, filesystems_ro)
