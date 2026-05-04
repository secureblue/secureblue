#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Replace existing container policies with the default policy"""

import filecmp
import os
import sys
from typing import Final

import sandbox
from utils import ToggleMode, print_err

# Use absolute paths
SYSTEM_POLICY_FILE: Final[str] = "/etc/containers/policy.json"
USER_POLICY_FILE: Final[str] = os.path.expanduser("~/.config/containers/policy.json")
MAX_POLICY_CONFIGS: Final[int] = 50
CONTAINER_FUNCTION: Final = \
    sandbox.SandboxedFunction(
        "container_policy.py",
        read_write_paths=["/etc/containers", "/usr/etc/containers"],
        capabilities=["CAP_DAC_OVERRIDE"]
    )

HELP_MESSAGE="""
Enables or disables the use of the Secureblue default container policy.
Old policies will be saved in their original directory as ".old" files.

usage:
ujust default-container-policy on
    Reverts to the system's default container policy.

ujust default-container-policy off
    Reverts to the previous, user-configured policy.

ujust default-container-policy status
    Reports if the current configuration is the default or a modified version.

ujust default-container-policy --help
    Prints this message.
"""

def deactivate_user_override() -> None:
    """Attempts to deactivate the current user's override policy"""

    if os.path.exists(USER_POLICY_FILE):
        if os.path.exists(f"{USER_POLICY_FILE}.old"):
            i = 1
            while os.path.exists(f"{USER_POLICY_FILE}.old.{i}") and i >= MAX_POLICY_CONFIGS:
                i += 1
            if i >= MAX_POLICY_CONFIGS:
                print_err("You have too many configurations.")
                print_err("Please visit ~/.config/containers to clean up old configurations.")
                print_err("ABORTING")
                return
            os.rename(USER_POLICY_FILE, f"{USER_POLICY_FILE}.old.{i}")
        else:
            os.rename(USER_POLICY_FILE, f"{USER_POLICY_FILE}.old")

def use_default_policy() -> None:
    """Attempts to convert the system global policy to the default"""

    if not filecmp.cmp(f"/usr{SYSTEM_POLICY_FILE}", SYSTEM_POLICY_FILE):
        if not os.path.exists(f"{SYSTEM_POLICY_FILE}.old"):
            # all requirements met
            sandbox.run(CONTAINER_FUNCTION, "normal")
        else:
            # An old config is already present
            sandbox.run(CONTAINER_FUNCTION, "multi-save")

def remove_default_policy() -> None:
    """Attempts to replace the default system policy with a previous, user-configed policy"""

    if filecmp.cmp(f"/usr{SYSTEM_POLICY_FILE}", SYSTEM_POLICY_FILE):
        if os.path.exists(f"{SYSTEM_POLICY_FILE}.old"):
            sandbox.run(CONTAINER_FUNCTION, "deactivate")
        else:
            print_err("No previous config was found.")
    else:
        print("You are already using a custom system policy.")

def main() -> int:
    """Main script entrypoint"""

    argc = len(sys.argv)
    argv = sys.argv

    required_args_count = 2
    if argc != required_args_count:
        print_err("Invalid args count for operation.")
        return 1

    valid_arguments = ["status", "help", "on", "off"]
    if argv[1] not in valid_arguments:
        print_err(f"Invalid argument, expected: {valid_arguments}")
        return 1

    match argv[1]:
        case ToggleMode.STATUS:
            system_policy_compare = filecmp.cmp(f"/usr{SYSTEM_POLICY_FILE}", SYSTEM_POLICY_FILE)
            user_policy_exists = not os.path.exists(USER_POLICY_FILE)
            if system_policy_compare and user_policy_exists:
                # prints "enabled" in OKGREEN
                print("\033[92menabled\033[0m")
            else:
                print_err("disabled")

        case ToggleMode.HELP:
            print(HELP_MESSAGE)

        case ToggleMode.ON:
            use_default_policy()
            deactivate_user_override()

        case ToggleMode.OFF:
            remove_default_policy()

    return 0

if __name__ == "__main__":
    sys.exit(main())
