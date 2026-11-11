#!/usr/bin/python3 -Es

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Add or remove the unfiltered Flathub remote."""

import json
import subprocess
import sys
from typing import TYPE_CHECKING, Final, assert_never

if TYPE_CHECKING:
    from files.system.usr.libexec.secureblue.shared import utils
else:
    from shared import utils

CommandUsageError: Final = utils.CommandUsageError
ToggleMode: Final = utils.ToggleMode
parse_basic_toggle_args: Final = utils.parse_basic_toggle_args
command_stdout: Final = utils.command_stdout
ask_yes_no: Final = utils.ask_yes_no

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
    remotes: list[str] = command_stdout(
        "flatpak", "remotes", "--user", "--columns=url,subset"
    ).splitlines()
    flathub_urls: list[str] = ["https://dl.flathub.org/repo/", "https://dl.flathub.org/beta-repo/"]

    for remote in remotes:
        url, subset = remote.split("\t")
        if url in flathub_urls and subset != "verified":
            return True

    return False


def print_remote_status() -> None:
    if unfiltered_remote_enabled():
        print("The unfiltered Flathub remote is enabled.")
    else:
        print("The unfiltered Flathub remote is disabled.")


def set_remote_unfiltered() -> None:
    if unfiltered_remote_enabled():
        print("The Flathub remote subset is already set to unfiltered.")
        return

    subprocess.run(
        [
            "/usr/bin/flatpak",
            "remote-modify",
            "--user",
            "--subset=",
            "flathub",
            "https://dl.flathub.org/repo/flathub.flatpakrepo",
        ],
        check=True,
    )

def is_verified(app: str) -> bool:
    app_verification_info = command_stdout(
        "curl", "-fLsS", "--retry", "5", f"https://flathub.org/api/v2/verification/{app}/status"
    )
    app_verification_info_json = json.loads(app_verification_info)
    return app_verification_info_json["verified"]

def set_remote_filtered() -> None:
    if not unfiltered_remote_enabled():
        print("The Flathub remote subset is already set to verified-only.")
        return
    
    installed_apps =
        [line.split("\t", 1) 
            for line 
                in command_stdout("flatpak", "list", "--app", "--columns=application,origin").splitlines()]

    flathub_installed_apps = [app for app, remote in installed_apps if origin == "flathub"]
    flathub_installed_verified_apps = [app for app in flathub_installed_apps if is_verified(app)]
    if flathub_installed_verified_apps:
        print("The following Flathub apps are unverified and will be removed by this action:")
        for unverified_app in flathub_installed_verified_apps
            print(f"  - {unverified_app}")

        if not ask_yes_no("Proceed?"):
            return
        
        subprocess.run(
            [
                "/usr/bin/flatpak",
                "uninstall",
                "--user",
                "-y",
                *flathub_installed_verified_apps
            ], 
            check=True
        )
    
    subprocess.run(
        [
            "/usr/bin/flatpak",
            "remote-modify",
            "--user",
            "--subset=verified",
            "flathub"
        ],
        check=True
    )

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
                set_remote_unfiltered()
            case ToggleMode.OFF:
                set_remote_filtered()
            case ToggleMode.STATUS:
                print_remote_status()
            case ToggleMode.HELP:
                print(HELP_MESSAGE)
            case _ as unreachable:
                assert_never(unreachable)
    except subprocess.CalledProcessError:
        print("An unexpected error occurred.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
