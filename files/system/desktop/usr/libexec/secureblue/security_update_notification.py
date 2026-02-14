#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import json
import sys
from enum import IntEnum, StrEnum, auto

from utils import command_stdout, command_succeeds

ALERT_ON_PACKAGE_UPGRADE = {
    "trivalent",
    "trivalent-subresource-filter"
}


class AdvisorySeverity(IntEnum):
    UNKNOWN = 0,
    LOW = 1,
    MODERATE = 2,
    IMPORTANT = 3,
    CRITICAL = 4,


class Action(IntEnum):
    REBOOT = auto(),
    SHOW_DETAILS = auto(),


class NotificationUrgency(StrEnum):
    NORMAL = auto(),
    CRITICAL = auto(),


def is_package_upgraded(target_packages: set(str)) -> bool:
    upgraded_packages = command_stdout(
        "rpm-ostree",
        "status",
        "--verbose",
        "--booted",
        "--jsonpath",
        ".cached-update.rpm-diff.upgraded",
    )

    if upgraded_packages == "[]":
        return False

    upgraded_packages = json.loads(upgraded_packages)

    # For each upgraded package
    for package in upgraded_packages[0]:
        # Extract package name
        package_name = package[1]

        if package_name in target_packages:
            return True

    return False


def advisory_patched() -> AdvisorySeverity | None:
    advisory_info = command_stdout(
            "rpm-ostree",
            "status",
            "--verbose",
            "--booted",
            "--jsonpath",
            ".cached-update.advisories"
    )

    if advisory_info == "[]":
        return None

    advisory_info = json.loads(advisory_info)

    max_severity = -1

    # For each advisory
    for advisory in advisory_info[0][0]:
        # Extract advisory severity
        severity = advisory[2]
        max_severity = max(max_severity, severity)
    
    return max_severity


def show_notification(urgency: NotificationUrgency) -> Action | None:
    # NULL cannot be int, but is returned if no option is selected.
    selection: str = command_stdout(
        "notify-send",
        f"--urgency={urgency}",
        "--expire-time=600000", # Timeout = 10 mins
        "--app-name=secureblue",
        "--action=Reboot",
        "--action=See CVE Details",
        "A {}security vulnerability has been patched".format(
            "major " if urgency == NotificationUrgency.CRITICAL else ""
        ),
        "Please reboot to run the updated system",
    )

    match selection:
        case "0":
            return Action.REBOOT
        case "1":
            return Action.SHOW_DETAILS
        case _:
            return None


def do_action(action: Action) -> None:
    match action:
        case Action.REBOOT:
            command_succeeds(
                "systemctl",
                "reboot",
            )
        case Action.SHOW_DETAILS:
            file_name = command_stdout(
                "mktemp",
                "--tmpdir",
                "rpm-ostree-status-XXXXXXXXXX.txt",
            )
            content = command_stdout(
                "rpm-ostree",
                "status",
                "--verbose",
                "--booted",
            )

            with open(file_name, "a") as f:
                f.write(content)

            command_succeeds(
                "xdg-open",
                f"{file_name}",
            )
        case None:
            pass


def main() -> int:
    advisory_severity = advisory_patched()

    if is_package_upgraded(ALERT_ON_PACKAGE_UPGRADE) | ( advisory_severity in {3, 4} ):
        do_action(show_notification(NotificationUrgency.CRITICAL))
    elif advisory_severity in {0, 1, 2}:
        do_action(show_notification(NotificationUrgency.NORMAL))

    return 0


if __name__ == "__main__":
    sys.exit(main())
