#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Add or remove the unfiltered Flathub remote."""

import subprocess
import sys
from typing import TYPE_CHECKING, Final, assert_never

if TYPE_CHECKING:
    from files.system.usr.libexec.secureblue import utils
else:
    import utils

CommandUsageError: Final = utils.CommandUsageError
ToggleMode: Final = utils.ToggleMode
parse_basic_toggle_args: Final = utils.parse_basic_toggle_args
command_stdout: Final = utils.command_stdout

HELP_MESSAGE: Final[str] = """\
Add or remove the unfiltered Flathub remote.

Usage:
ujust set-flathub-unfiltered
    Adds or removes interactively based on the user's preference.

ujust set-flathub-unfiltered on
    Adds the unfiltered Flathub remote; does nothing if it is already present.

ujust set-flathub-unfiltered off
    Removes the unfiltered Flathub remote; does nothing if it is already removed.

ujust set-flathub-unfiltered status
    Reports whether the unfiltered Flathub remote is present on the system.

ujust set-flathub-unfiltered --help
    Prints this message.
"""


def unfiltered_remote_enabled() -> bool:
    remotes: list[str] = command_stdout("flatpak", "remotes", "--columns=url,subset").splitlines()
    flathub_urls: list[str] = ["https://dl.flathub.org/repo/", "https://dl.flathub.org/beta-repo/"]

    for remote in remotes:
        url, subset = remote.split("\t")
        if url in flathub_urls and subset != "verified":
            return True

    return False


def unfiltered_remote_print_status() -> None:
    if unfiltered_remote_enabled():
        print("The unfiltered Flathub remote is enabled.")
    else:
        print("The unfiltered Flathub remote is disabled.")


def add_unfiltered_remote() -> None:
    if unfiltered_remote_enabled():
        print("The unfiltered Flathub remote has already been added to the system.")
        return

    subprocess.run(
        [
            "/usr/bin/flatpak",
            "remote-add",
            "--if-not-exists",
            "--user",
            "flathub",
            "https://dl.flathub.org/repo/flathub.flatpakrepo",
        ],
        check=True,
    )


def remove_unfiltered_remote() -> None:
    if not unfiltered_remote_enabled():
        print("The unfiltered Flathub remote has already been removed from the system.")
        return

    subprocess.run(["/usr/bin/flatpak", "remote-delete", "--user", "flathub"], check=True)


def main() -> int:
    try:
        mode = parse_basic_toggle_args(
            prompt="Would you like to have the unfiltered Flathub remote available?"
        )
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2

    try:
        match mode:
            case ToggleMode.ON:
                add_unfiltered_remote()
            case ToggleMode.OFF:
                remove_unfiltered_remote()
            case ToggleMode.STATUS:
                unfiltered_remote_print_status()
            case ToggleMode.HELP:
                print(HELP_MESSAGE)
            case _ as unreachable:
                assert_never(unreachable)
    except subprocess.CalledProcessError:
        print("An unexpected error occured.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
