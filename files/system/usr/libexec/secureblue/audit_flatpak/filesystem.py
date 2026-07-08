#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Filesystem-specific Flatpak permissions checks for secureblue auditing script.
"""

from dataclasses import KW_ONLY, InitVar, dataclass, field
from dataclasses import replace as dataclass_replace
from typing import Final

from auditor import Note, Recommendation, Status, gettext_marker

from . import ARBITRARY_PERMISSIONS_EXPECTED, FlatpakPermissionsState, PermissionCheck, Permissions

_: Final = gettext_marker()

PASS: Final = Status.PASS
INFO: Final = Status.INFO
WARN: Final = Status.WARN
FAIL: Final = Status.FAIL

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


@dataclass(frozen=True)
class Filesystem:
    """A fully parsed filesystem permission."""

    perm: InitVar[str]
    # perm string should be only constructor argument

    canon_path: str = field(init=False)
    aliased_path: str = field(init=False)
    is_aliased: bool = field(init=False, default=False)

    negated: bool = field(init=False)
    readonly: bool = field(init=False)

    def __post_init__(self, perm: str) -> None:
        """
        Parse filesystem permission string.

        This should effectively match Flatpak parsing:
        https://github.com/flatpak/flatpak/blob/1.17.7/common/flatpak-context.c#L1648
        """
        object.__setattr__(self, "readonly", perm.endswith(":ro"))
        object.__setattr__(self, "negated", perm.startswith("!"))
        if perm.endswith(":ro"):
            path = perm.removesuffix(":ro")
        elif perm.endswith(":rw"):
            path = perm.removesuffix(":rw")
        elif perm.endswith(":create"):
            path = perm.removesuffix(":create")
        else:
            path = perm

        path = path.removeprefix("!").rstrip("/")
        object.__setattr__(self, "aliased_path", path)

        for name, alias in ALIASES.items():
            if path.startswith(alias):
                path = path.replace(alias, name, 1)
                object.__setattr__(self, "is_aliased", True)
                break
        object.__setattr__(self, "canon_path", path)


FilesystemPerms = dict[str, Filesystem]
"""
Mapping of filesystem permission information, accessed using their canonical path.

For example, to check if "host-os" exists at all in the permissions list,
one can simply do ("host-os" in FilesystemPerms), avoiding iteration.
"""


def _check_hardened_malloc_access(
    state: FlatpakPermissionsState, filesystem_perms: FilesystemPerms
) -> None:
    if not filesystem_perms or "host-os" not in filesystem_perms:
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
    state: FlatpakPermissionsState, filesystem_perms: FilesystemPerms
) -> None:
    if state.name in ARBITRARY_PERMISSIONS_EXPECTED:
        return

    override_path = "xdg-data/flatpak/overrides"
    if override_path not in filesystem_perms:
        return

    set_permission = filesystem_perms[override_path]
    if set_permission.readonly:
        return

    state.arbitrary_permissions = True
    note = Note(_("{0} can modify flatpak permissions.").format(state.name), status=FAIL)
    rec_lines = (
        _("The following flatpak app(s) can modify flatpak permissions:"),
        Recommendation.NAMES_PLACEHOLDER,
        _("This grants the ability to acquire arbitrary permissions."),
        _("To remove this permission from an app, use Flatseal or run:"),
        f"$ flatpak override -u --nofilesystem={set_permission.aliased_path} com.example.Example",
        _('(replacing "{0}" with the flatpak app ID)').format("com.example.Example"),
    )
    rec = Recommendation("\n".join(rec_lines), mergeable_name=state.name)
    state.update(note=note, rec=rec)


@dataclass(frozen=True)
class DirectoryCheck(PermissionCheck):
    """Variant of PermissionCheck specific to filesystem permissions."""

    _: KW_ONLY  # Avoids interfering with PermissionCheck positional arguments

    category: str = field(init=False, default="filesystems")

    path: str = field(init=False)
    """Less ambiguous alias for "permission", which could be mistaken for rwx permissions."""

    description: str | None = None
    """None shows the exact path, preventing grouping aliases into one recommendation."""

    _comment_already_prefixed: bool = False

    def __post_init__(self) -> None:
        """Sets derived fields."""
        object.__setattr__(self, "path", self.permission)

        has_comment = hasattr(self, "comment") and self.comment is not None
        if not has_comment:
            return
        if not self._comment_already_prefixed:
            template = _("This grants access to {0}.").format(self.comment)
            object.__setattr__(self, "comment", template)
            object.__setattr__(self, "_comment_already_prefixed", True)


DANGEROUS_DIRECTORY_CHECKS: list[DirectoryCheck] = [
    DirectoryCheck("host", FAIL, _("all system files")),
    DirectoryCheck("home", FAIL, _("all user files")),
    DirectoryCheck("xdg-config", FAIL, _("other applications' configuration files")),
    DirectoryCheck("xdg-cache", FAIL, _("other applications' cache files")),
    DirectoryCheck("xdg-data", FAIL, _("other applications' data files")),
]


def _check_dangerous_dirs(
    state: FlatpakPermissionsState, filesystem_perms: FilesystemPerms
) -> None:
    for d in DANGEROUS_DIRECTORY_CHECKS:
        dir_check = d  # avoids reassigning loop variable

        canon_path = dir_check.path
        if canon_path not in filesystem_perms:
            continue
        perm = filesystem_perms[canon_path]

        if perm.is_aliased:
            dir_check = dataclass_replace(dir_check, permission=perm.aliased_path)
        state.update(note=dir_check.note(state.name), rec=dir_check.recommendation(state.name))


def check_fs_permissions(state: FlatpakPermissionsState, perms: Permissions) -> None:
    filesystem_perms: FilesystemPerms = {}

    perm_strings = perms.permissions.get("filesystems")
    if perm_strings is None:
        _check_hardened_malloc_access(state, filesystem_perms)
        return

    for perm_string in perm_strings:
        perm = Filesystem(perm_string)
        if perm.negated:
            continue
        filesystem_perms[perm.canon_path] = perm

    _check_hardened_malloc_access(state, filesystem_perms)
    _check_overrides_access(state, filesystem_perms)
    _check_dangerous_dirs(state, filesystem_perms)
