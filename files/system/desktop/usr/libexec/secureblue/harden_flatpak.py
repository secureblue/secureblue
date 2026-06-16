#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import contextlib
import os
import re
import subprocess
import sys
from typing import TYPE_CHECKING, Final

from flatpak_utils import flatpak_override, installed_app_list, resolve_app_id

if TYPE_CHECKING:
    from files.system.usr.libexec.secureblue import utils
else:
    import utils

command_stdout: Final = utils.command_stdout
print_wrapped: Final = utils.print_wrapped

DESCRIPTION: Final[str] = """
Harden flatpaks by preloading hardened_malloc, using the highest supported
hardware capabilities. When called with a flatpak application ID as an
argument, it applies the override to that application instead of globally.
"""


def best_microarch() -> str | None:
    """Get best microarchitecture for system."""
    try:
        ld_info = command_stdout("/usr/lib64/ld-linux-x86-64.so.2", "--help")
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    m = re.search(
        r"^\s*(x86-64-v\d+).*\(supported, searched\)", ld_info, flags=re.ASCII | re.MULTILINE
    )
    return m and m.group(1)


def libhardened_malloc_path(uarch: str | None) -> str:
    """Get path to libhardened_malloc.so"""
    directory = "/var/run/host/usr/lib64"
    if uarch is not None:
        directory += f"/glibc-hwcaps/{uarch}"
    return f"{directory}/libhardened_malloc.so"


def current_override_status(app_id: str, hmalloc_path: str) -> tuple[bool, bool]:
    """Get current host-os and LD_PRELOAD override status"""
    override_dir = os.path.expanduser("~/.local/share/flatpak/overrides")
    host_os_access = False
    ld_preload_set = False
    host_os_pattern = re.compile(r"filesystems=(?:.*;)?host-os(?::ro)?(?:;.*)?\n")
    ld_preload_pattern = re.compile(rf"LD_PRELOAD=(?:.*\s)?{re.escape(hmalloc_path)}(?:\s.*)?\n")
    with (
        contextlib.suppress(FileNotFoundError),
        open(f"{override_dir}/{app_id}", encoding="utf8") as f,
    ):
        for line in f:
            if re.fullmatch(host_os_pattern, line):
                host_os_access = True
            if re.fullmatch(ld_preload_pattern, line):
                ld_preload_set = True
    return host_os_access, ld_preload_set


def remove_overrides_from_file(override_file: str, *, no_host_os: bool, ld_preload: bool) -> None:
    """Remove selected overrides from flatpak override file at given path."""
    if not no_host_os and not ld_preload:
        return

    file_modified = False
    modified_contents = ""
    with open(override_file, encoding="utf8") as f:
        for line in f:
            if no_host_os and line.startswith("filesystems="):
                line, subs = re.subn(r"!host-os(?:;|$)", "", line)  # noqa: PLW2901
                if subs > 0:
                    file_modified = True
            elif ld_preload and line.startswith("LD_PRELOAD="):
                file_modified = True
                continue
            modified_contents += line

    if file_modified:
        with open(override_file, "w", encoding="utf8") as f:
            f.write(modified_contents)


def harden_flatpak_app(app_id: str, hmalloc_path: str) -> None:
    """Applied hardened_malloc to flatpak app with given app ID."""
    override_dir = os.path.expanduser("~/.local/share/flatpak/overrides")
    overrides_to_apply = []
    global_host_os_access, global_ld_preload = current_override_status("global", hmalloc_path)

    with contextlib.suppress(FileNotFoundError):
        remove_overrides_from_file(
            f"{override_dir}/{app_id}",
            no_host_os=global_host_os_access,
            ld_preload=global_ld_preload,
        )

    if not global_host_os_access:
        overrides_to_apply.append("--filesystem=host-os:ro")

    if not global_ld_preload:
        overrides_to_apply.append(f"--env=LD_PRELOAD={hmalloc_path}")

    if overrides_to_apply:
        flatpak_override(*overrides_to_apply, app_id)


def main() -> int:
    """Main entry point for script."""
    parser = argparse.ArgumentParser(prog="ujust harden-flatpak", description=DESCRIPTION)
    parser.add_argument("app_id", nargs="?", metavar="APP_ID", help="app ID of flatpak to harden")
    args = parser.parse_args()

    uarch = best_microarch()
    hmalloc_path = libhardened_malloc_path(uarch)
    hmalloc_description = "hardened_malloc" if uarch is None else f"hardened_malloc (µarch {uarch})"
    host_os_note = """
    Note: the filesystem=host-os:ro permission has also been granted. This gives read-only
    access to /usr, which is where the hardened_malloc shared library is installed.
    """

    if not args.app_id:
        flatpak_override(
            "--filesystem=host-os:ro",
            f"--env=LD_PRELOAD={hmalloc_path}",
            "--env=ELECTRON_OZONE_PLATFORM_HINT=auto",
        )
        print(f"{hmalloc_description} applied to all flatpaks by default.")
        print()
        print_wrapped(host_os_note)
        print()
        print_wrapped(
            """
            ELECTRON_OZONE_PLATFORM_HINT=auto has also been set for all flatpaks, ensuring that
            older Electron flatpaks prefer Wayland over X11. (This is already the default for
            newer Electron apps.)
            """
        )
        return 0

    installed_app_ids = installed_app_list()
    app_id = resolve_app_id(args.app_id, installed_app_ids)
    if app_id is None:
        print("No matching app IDs found; exiting.")
        return 1
    harden_flatpak_app(app_id, hmalloc_path)
    print(f"{hmalloc_description} applied to flatpak {app_id}")
    print()
    print_wrapped(host_os_note)

    return 0


if __name__ == "__main__":
    sys.exit(main())
