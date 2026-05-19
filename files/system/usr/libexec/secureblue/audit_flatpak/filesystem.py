#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Filesystem-specific Flatpak permissions checks for secureblue auditing script.
"""

from dataclasses import KW_ONLY, dataclass, field
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


def _parse_fs_permission(perm: str) -> tuple[str, bool, bool, str | None]:
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
    aliased_path = None
    for name, alias in ALIASES.items():
        if path.startswith(alias):
            aliased_path = path
            path = path.replace(alias, name, 1)
            break
    return path, readonly, negated, aliased_path


def _check_dangerous_dirs(
    state: FlatpakPermissionsState, filesystems_rw_aliasmap: dict[str, str | None]
) -> None:
    for d in DANGEROUS_DIRECTORY_CHECKS:
        dir_check = d  # avoids reassigning loop variable
        canon_path = dir_check.path
        if canon_path not in filesystems_rw_aliasmap:
            continue
        aliased_path = filesystems_rw_aliasmap[canon_path]
        if aliased_path is not None:
            dir_check = dataclass_replace(dir_check, permission=aliased_path)
        state.update(
            note=dir_check.note(state.name), rec=dir_check.recommendation(state.name)
        )


def _check_hardened_malloc_access(
    state: FlatpakPermissionsState,
    filesystems: list[str] | None,
    filesystem_perms: dict[str, str | None],

) -> None:
    if filesystems is None or (
        "host-os" not in filesystem_perms
    ):
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
    state: FlatpakPermissionsState, filesystems_rw_aliasmap: dict[str, str | None]
) -> None:
    if state.name in ARBITRARY_PERMISSIONS_EXPECTED:
        return
    override_path = "xdg-data/flatpak/overrides"
    if override_path not in filesystems_rw_aliasmap:
        return
    state.arbitrary_permissions = True
    override_path = filesystems_rw_aliasmap[override_path] or override_path
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


def check_fs_permissions(state: FlatpakPermissionsState, perms: Permissions) -> None:
    perm_strings = perms.permissions.get("filesystems")
    filesystem_perms = {}

    if perm_strings is None:
        _check_hardened_malloc_access(state, filesystem_perms)
        return
    for perm_string in perm_strings:
        path, readonly, negated, aliased_path = _parse_fs_permission(perm_string)
        if negated:
            continue
        if readonly:
            filesystem_perms[path] = aliased_path
        else:
            filesystem_perms[path] = aliased_path
    _check_dangerous_dirs(state, filesystem_perms)
    _check_overrides_access(state, filesystem_perms)
    _check_hardened_malloc_access(
        state, perm_strings, filesystem_perms
    )
