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


class AdvisorySeverity(StrEnum):
    UNKNOWN = auto(),
    LOW = auto(),
    MODERATE = auto(),
    IMPORTANT = auto(),
    CRITICAL = auto(),


class Action(IntEnum):
    REBOOT = auto(),
    SHOW_DETAILS = auto(),


class NotificationUrgency(StrEnum):
    NORMAL = auto(),
    CRITICAL = auto(),


def is_package_upgraded(target_packages: set(str)) -> bool:
    upgraded_packages = json.loads(
        command_stdout(
            "rpm-ostree",
            "status",
            "--verbose",
            "--booted",
            "--jsonpath",
            ".cached-update.rpm-diff.upgraded",
        )
    )

    try:
        # For each upgraded package
        for i in range(len(upgraded_packages[0])):
            # Extract package name
            package_name = upgraded_packages[0][i][1]

            if package_name in target_packages:
                return True
    except IndexError:
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

    try:
        # For each advisory
        for i in range(len(advisory_info[0][0])):
            # Extract advisory severity
            match advisory_info[0][i][2]:
                case 4:
                    return AdvisorySeverity.CRITICAL
                case 3:
                    return AdvisorySeverity.IMPORTANT
                case 2:
                    return AdvisorySeverity.MODERATE
                case 1:
                    return AdvisorySeverity.LOW
                case 0:
                    return AdvisorySeverity.UNKNOWN
                case _:
                    sys.exit(1) # Should not reach this.
    except IndexError:
        sys.exit(1) # Should not reach as advisory_info != "[]"


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

    if is_package_upgraded(ALERT_ON_PACKAGE_UPGRADE) | ( advisory_severity in {"important", "critical"} ):
        do_action(show_notification(NotificationUrgency.CRITICAL))
    elif advisory_severity in {"unknown", "low", "moderate"}:
        do_action(show_notification(NotificationUrgency.NORMAL))

    sys.exit(0)


if __name__ == "__main__":
    main()
