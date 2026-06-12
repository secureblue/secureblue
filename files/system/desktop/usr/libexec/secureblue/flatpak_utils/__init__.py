#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Various utility functions used in secureblue flatpak scripts.
"""

import subprocess
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from files.system.usr.libexec.secureblue import utils
else:
    import utils

command_stdout: Final = utils.command_stdout
print_wrapped: Final = utils.print_wrapped


def flatpak_override(*args: str) -> None:
    """Apply flatpak overrides."""
    subprocess.run(["/usr/bin/flatpak", "override", "--user", *args], check=True)


def installed_app_list() -> list[str]:
    """Get list of installed flatpak app IDs."""
    return command_stdout("/usr/bin/flatpak", "list", "--columns=application", "--app").splitlines()


def resolve_app_id(provided: str, installed_app_ids: list[str]) -> str | None:
    """Determine app ID intended by user."""
    # First, return exact match if found.
    if provided in installed_app_ids:
        return provided

    # Next, try case-insensitive matches.
    provided = provided.casefold()
    matches = [app_id for app_id in installed_app_ids if app_id.casefold() == provided]
    # If there's exactly one case-insensitive match, just choose it, don't prompt the user.
    if len(matches) == 1:
        return matches[0]

    print_wrapped(f"'{provided}' is not the application ID of an installed flatpak.")

    # If there's no case-insensitive matches, try substring matches.
    if not matches:
        matches = [app_id for app_id in installed_app_ids if provided in app_id.casefold()]

    if not matches:
        return None

    # very slow import, so only load once needed
    import inquirer  # noqa: PLC0415

    question = inquirer.List(
        "app_id", message="Did you mean one of the following? (Ctrl+C to cancel)", choices=matches
    )
    answer = inquirer.prompt([question])
    return None if answer is None else answer["app_id"]
