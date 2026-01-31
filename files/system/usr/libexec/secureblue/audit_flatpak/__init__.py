#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Flatpak permissions checks for secureblue auditing script.
"""

from dataclasses import dataclass, field
from typing import Final

from auditor import Note, Recommendation, Status, gettext_marker

_: Final = gettext_marker()

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


def _parse_config_sections(conf_text: str) -> dict[str | None, dict[str, str]]:
    """Parse config file into sections containing key-value mappings"""
    sections = {}
    current_section = None
    for raw_line in conf_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
            sections[current_section] = {}
            continue
        key, value = line.split("=", maxsplit=1)
        sections[current_section][key] = value
    return sections


def parse_flatpak_permissions(perms_text: str) -> Permissions:
    """Get permissions for an installed flatpak."""
    perms = Permissions()
    sections = _parse_config_sections(perms_text)
    for section, lines in sections.items():
        match section:
            case "Session Bus Policy":
                perms.session_bus_talk = [key for key, value in lines.items() if value == "talk"]
                perms.session_bus_own = [key for key, value in lines.items() if value == "own"]
            case "System Bus Policy":
                perms.system_bus_talk = [key for key, value in lines.items() if value == "talk"]
                perms.system_bus_own = [key for key, value in lines.items() if value == "own"]
            case "Environment":
                perms.environment = lines
            case _:
                for key, value in lines.items():
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
    comment: str | None = None
    endnote: str | None = None
    sandbox_escape: bool = False
    arbitrary_permissions: bool = False

    def default_description(self) -> str:
        """Default description if other description isn't provided."""
        perm_type = FLATPAK_OVERRIDE_OPTIONS[self.category][0]
        return f"{perm_type}={self.permission} " + _("permission")

    def note(self, name: str) -> Note:
        """Generate the note for if the check fails."""
        description = self.description or self.default_description()
        return Note(_("{0} has {1}").format(name, description), status=self.status)

    def recommendation(self, name: str) -> Recommendation:
        """Give the recommendation for if the check fails."""
        if self.sandbox_escape:
            sandbox_escape_note = _("This may also be used as a sandbox escape vector.")
        else:
            sandbox_escape_note = ""
        option = FLATPAK_OVERRIDE_OPTIONS[self.category][1]
        description = self.description or self.default_description()
        rec_lines = (
            _("The following flatpak app(s) have {0}:").format(description),
            Recommendation.NAMES_PLACEHOLDER,
            self.comment or "",
            sandbox_escape_note,
            _("To remove this permission from an app, use Flatseal or run:"),
            f"$ flatpak override -u --{option}={self.permission} com.example.Example",
            _('(replacing "{0}" with the flatpak app ID)').format("com.example.Example"),
            self.endnote or "",
        )
        rec = "\n".join(line.strip() for line in rec_lines if line.strip())
        return Recommendation(rec, mergeable_name=name)


@dataclass(frozen=True)
class DirectoryInfo:
    """Info about a directory to check."""

    path: str
    description: str
    status: Status


FLATPAK_PERMISSION_CHECKS: list[PermissionCheck] = [
    PermissionCheck("shared", "network", INFO, _("network access")),
    PermissionCheck("shared", "ipc", INFO, _("inter-process communications access")),
    PermissionCheck("sockets", "x11", FAIL, _("X11 access")),
    PermissionCheck("sockets", "pulseaudio", WARN, _("access to the PulseAudio socket")),
    PermissionCheck(
        "sockets",
        "session-bus",
        FAIL,
        _("access to the D-Bus session bus"),
        comment=_("This grants access to audio and microphones."),
    ),
    PermissionCheck("sockets", "system-bus", FAIL, _("access to the D-Bus system bus")),
    PermissionCheck("sockets", "ssh-auth", WARN, _("access to the SSH agent")),
    PermissionCheck(
        "devices",
        "all",
        FAIL,
        comment=_("This grants access to input devices, GPUs, raw USB, and virtualization."),
        sandbox_escape=True,
        endnote=_("If GPU access is required, allow {0} instead.").format("device=dri"),
    ),
    PermissionCheck("devices", "input", INFO, comment=_("This grants access to input devices.")),
    PermissionCheck(
        "devices", "kvm", WARN, comment=_("This grants access to kernel-based virtualization.")
    ),
    PermissionCheck(
        "devices",
        "shm",
        FAIL,
        comment=_("This grants access to shared memory."),
        sandbox_escape=True,
    ),
    PermissionCheck(
        "devices",
        "usb",
        WARN,
        comment=_("This grants raw USB device access."),
        sandbox_escape=True,
    ),
    PermissionCheck("features", "bluetooth", WARN, _("bluetooth access")),
    PermissionCheck("features", "devel", WARN, _("ptrace access")),
]

ARBITRARY_PERMISSIONS_EXPECTED: list[str] = [
    "com.github.tchx84.Flatseal",
    "io.github.flattool.Warehouse",
    "io.github.kolunmi.Bazaar",
]


@dataclass
class FlatpakPermissionsState:
    """The state of a flatpak's permissions."""

    name: str
    notes: list[Note] = field(default_factory=list)
    recs: list[Recommendation] = field(default_factory=list)
    status: Status = PASS
    arbitrary_permissions: bool = False

    def update(self, note: Note, rec: Recommendation | None = None) -> None:
        """Add note and recommendation, and adjust status."""
        self.notes.append(note)
        if note.status is not None:
            self.status = self.status.downgrade_to(note.status)
        if rec is not None:
            self.recs.append(rec)


def check_flatpak_permissions(
    name: str, perms: Permissions, bluetooth_loaded: bool, ptrace_allowed: bool
) -> FlatpakPermissionsState:
    """Check permissions for a single flatpak."""
    flatpak_permissions_state = FlatpakPermissionsState(name)

    _check_predefined_flatpak_permissions(
        flatpak_permissions_state, perms, bluetooth_loaded, ptrace_allowed
    )
    _check_fs_permissions(flatpak_permissions_state, perms)
    _handle_flatpak_buses(flatpak_permissions_state, perms)
    _check_ld_preload(flatpak_permissions_state, perms)
    _handle_arbitrary_permissions(flatpak_permissions_state)

    return flatpak_permissions_state


def _handle_arbitrary_permissions(state: FlatpakPermissionsState) -> None:
    if state.arbitrary_permissions:
        note = _("{0} can acquire arbitrary permissions.").format(state.name)
        if state.name in ARBITRARY_PERMISSIONS_EXPECTED:
            status = INFO
            note += "\n" + _("However, this is required for its functionality.")
        else:
            status = FAIL
        state.update(Note(note, status=status))


def _check_ld_preload(state: FlatpakPermissionsState, perms: Permissions) -> None:
    ld_preload = perms.environment.get("LD_PRELOAD")
    if ld_preload is None:
        ld_preload_files = []
    else:
        ld_preload_files = [s.rsplit("/", maxsplit=1)[-1] for s in ld_preload.split()]
    if "libhardened_malloc.so" in ld_preload_files:
        return
    if "libhardened_malloc-light.so" in ld_preload_files:
        status = INFO
        extra_note = Note(
            _("{0} is requesting {1}").format(state.name, "hardened_malloc-light"), status=INFO
        )
    elif "libhardened_malloc-pkey.so" in ld_preload_files:
        status = INFO
        extra_note = Note(
            _("{0} is requesting {1}").format(state.name, "hardened_malloc-pkey"), status=INFO
        )
    else:
        status = WARN
        extra_note = None

    note = Note(_("{0} is not requesting {1}").format(state.name, "hardened_malloc"), status=status)
    rec_lines = (
        _("The following flatpak app(s) are not requesting {0}:").format("hardened_malloc"),
        Recommendation.NAMES_PLACEHOLDER,
        _("To enable it for an app, run:"),
        "$ ujust harden-flatpak com.example.Example",
        _('(replacing "{0}" with the flatpak app ID)').format("com.example.Example"),
    )
    rec = Recommendation("\n".join(rec_lines), mergeable_name=state.name)
    state.update(note=note, rec=rec)
    if extra_note is not None:
        state.update(extra_note)


def _bus_grants_arbitrary_permissions(name: str, is_session: bool) -> bool:
    """Test if bus name grants arbitrary permissions."""
    # Ported from Flathub website source code:
    # https://github.com/flathub-infra/website/blob/c9b16cd964c0a6166f157bb05fb91375b61e01cd/frontend/src/safety.ts#L406-L431
    # Used under the terms of the Apache-2.0 license.
    bus_prefixes = ("org.freedesktop.Flatpak.", "org.freedesktop.DBus.")
    bus_names = (
        "org.freedesktop.*",
        "org.gnome.*",
        "org.kde.*",
        "org.freedesktop.DBus",
        "org.freedesktop.systemd1",
        "org.freedesktop.login1",
        "org.kde.KWin",
        "org.kde.plasmashell",
    )
    session_bus_names = ("org.freedesktop.Flatpak", "org.freedesktop.impl.portal.PermissionStore")
    return (
        any(name.startswith(prefix) for prefix in bus_prefixes)
        or name in bus_names
        or (is_session and name in session_bus_names)
    )


def _handle_flatpak_buses(state: FlatpakPermissionsState, perms: Permissions) -> None:
    present_dangerous_buses = [
        (bus_name, True)
        for bus_name in perms.session_bus_talk
        if _bus_grants_arbitrary_permissions(bus_name, is_session=True)
    ]
    present_dangerous_buses += [
        (bus_name, False)
        for bus_name in perms.system_bus_talk
        if _bus_grants_arbitrary_permissions(bus_name, is_session=False)
    ]
    for bus_name, is_session in present_dangerous_buses:
        state.arbitrary_permissions = True
        if state.name not in ARBITRARY_PERMISSIONS_EXPECTED:
            if is_session:
                note = _("{0} can talk to {1} on the session bus.").format(state.name, bus_name)
                first_line = _("The following flatpak app(s) can talk to {0} on the session bus:")
                option = "no-talk-name"
            else:
                note = _("{0} can talk to {1} on the system bus.").format(state.name, bus_name)
                first_line = _("The following flatpak app(s) can talk to {0} on the system bus:")
                option = "system-no-talk-name"
            rec_lines = (
                first_line.format(bus_name),
                Recommendation.NAMES_PLACEHOLDER,
                _("This grants the ability to acquire arbitrary permissions."),
                _("To remove this permission from an app, use Flatseal or run:"),
                f"$ flatpak override -u --{option}={bus_name} com.example.Example",
                _('(replacing "{0}" with the flatpak app ID)').format("com.example.Example"),
            )
            state.update(
                note=Note(note, status=FAIL),
                rec=Recommendation("\n".join(rec_lines), mergeable_name=state.name),
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
) -> None:
    for check in FLATPAK_PERMISSION_CHECKS:
        if _predefined_check_applies(check, existing_permissions, bluetooth_loaded, ptrace_allowed):
            state.update(note=check.note(state.name), rec=check.recommendation(state.name))
            state.arbitrary_permissions |= check.arbitrary_permissions


def _check_dangerous_dirs(state: FlatpakPermissionsState, filesystems_rw: dict[str, bool]) -> None:
    dangerous_dirs: list[DirectoryInfo] = [
        DirectoryInfo("host", _("all system files"), FAIL),
        DirectoryInfo("home", _("all user files"), FAIL),
        DirectoryInfo("xdg-config", _("other applications' configuration files"), FAIL),
        DirectoryInfo("xdg-cache", _("other applications' cache files"), FAIL),
        DirectoryInfo("xdg-data", _("other applications' data files"), FAIL),
    ]

    for directory in dangerous_dirs:
        if directory.path in filesystems_rw:
            aliased_path = directory.path
            is_alias = filesystems_rw[directory.path]
            if is_alias:
                aliased_path = directory.path.replace(directory.path, ALIASES[directory.path], 1)
            note = Note(
                _("{0} has {1} permission").format(state.name, f"filesystem={directory.path}"),
                status=directory.status,
            )
            rec_lines = (
                _("The following flatpak app(s) have {0} permission:").format(
                    f"filesystem={aliased_path}"
                ),
                Recommendation.NAMES_PLACEHOLDER,
                _("This grants access to {0}.").format(directory.description),
                _("To remove this permission from an app, use Flatseal or run:"),
                f"$ flatpak override -u --nofilesystem={aliased_path} com.example.Example",
                _('(replacing "{0}" with the flatpak app ID)').format("com.example.Example"),
            )
            rec = Recommendation("\n".join(rec_lines), mergeable_name=state.name)
            state.update(note=note, rec=rec)


def _check_hardened_malloc_access(
    state: FlatpakPermissionsState,
    filesystems: list[str] | None,
    filesystems_rw: dict[str, bool],
    filesystems_ro: dict[str, bool],
) -> None:
    if filesystems is None or ("host-os" not in filesystems_ro and "host-os" not in filesystems_rw):
        note = Note(
            _("{0} is missing {1} permission").format(state.name, "host-os:ro"), status=WARN
        )
        rec_lines = (
            _("The following flatpak app(s) are missing {0} permission:").format("host-os:ro"),
            Recommendation.NAMES_PLACEHOLDER,
            _("This is required to load hardened_malloc."),
            _("To add this permission to an app, use Flatseal or run:"),
            "$ flatpak override -u --filesystem=host-os:ro com.example.Example",
            _('(replacing "{0}" with the flatpak app ID)').format("com.example.Example"),
        )
        rec = Recommendation("\n".join(rec_lines), mergeable_name=state.name)
        state.update(note=note, rec=rec)


def _check_overrides_access(
    state: FlatpakPermissionsState, filesystems_rw: dict[str, bool]
) -> None:
    override_path = "xdg-data/flatpak/overrides"
    if override_path in filesystems_rw:
        state.arbitrary_permissions = True
        is_alias = filesystems_rw[override_path]
        if is_alias:
            override_path = override_path.replace("xdg-data", ALIASES["xdg-data"], 1)
        if state.name not in ARBITRARY_PERMISSIONS_EXPECTED:
            note = Note(_("{0} can modify flatpak permissions.").format(state.name), status=FAIL)
            rec_lines = (
                _("The following flatpak app(s) can modify flatpak permissions:"),
                Recommendation.NAMES_PLACEHOLDER,
                _("This grants the ability to acquire arbitrary permissions."),
                _("To remove this permission from an app, use Flatseal or run:"),
                f"$ flatpak override -u --nofilesystem={override_path} com.example.Example",
                _('(replacing "{0}" with the flatpak app ID)').format("com.example.Example"),
            )
            rec = Recommendation("\n".join(rec_lines), mergeable_name=state.name)
            state.update(note=note, rec=rec)


def _check_fs_permissions(state: FlatpakPermissionsState, perms: Permissions) -> None:
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
