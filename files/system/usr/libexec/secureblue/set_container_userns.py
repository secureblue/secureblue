#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Enable, disable, or check status of container-domain user namespace creation."""

import subprocess  # nosec
import sys
from typing import Final

import sandbox
from utils import (
    CommandUsageError,
    ToggleMode,
    ask_yes_no,
    command_succeeds,
    parse_basic_toggle_args,
    print_wrapped,
)

HELP_MESSAGE: Final[str] = """\
Toggles if container-domain user namespace creation is allowed.

usage:
ujust set-container-userns
    Enables or disables interactively based on the user's preference.

ujust set-container-userns on
    Enables container-domain userns creation; does nothing if already on.

ujust set-container-userns off
    Disables container-domain userns creation; does nothing if already off.

ujust set-container-userns status
    Reports if container-domain userns creation is enabled or disabled.

ujust set-container-userns --help
    Prints this message.
"""

CONTAINER_USERNS_MODULE: Final[str] = "harden_container_userns"


def container_userns_enabled() -> bool:
    """Return whether container-domain user namespace creation is enabled."""
    # First try to read the list of enabled SELinux modules directly.
    semodule_proc = subprocess.run(
        ["/usr/bin/semodule", "-l"], check=False, capture_output=True, text=True
    )  # nosec
    if semodule_proc.returncode == 0:
        return CONTAINER_USERNS_MODULE not in semodule_proc.stdout.splitlines()

    # If we can't run `semodule -l`, we're running unprivileged and therefore we check
    # whether `podman unshare true` succeeds, which lets us infer the state of the module.
    return command_succeeds("/usr/bin/podman", "unshare", "/usr/bin/true")


def stop_containers(*, prompt: bool = True) -> bool:
    """
    Stop all containers and shut down podman, optionally asking the user for confirmation.
    Return value is False if the user chooses not to proceed, True otherwise.
    """
    if prompt:
        print("Warning: This will stop ALL containers and shut down podman.")
        if not ask_yes_no("Are you sure you want to do this?"):
            return False
    print("Stopping all containers and shutting down podman...")
    subprocess.run(["/usr/bin/podman", "stop", "--all"], check=True)  # nosec
    subprocess.run(["/usr/bin/killall", "catatonit"], check=False)  # nosec
    if command_succeeds("/usr/bin/pgrep", "catatonit"):
        print_wrapped("""
            Warning: Catatonit running as another user detected.
            Reboot your machine to reset podman state.
        """)
    return True


semodule_function = sandbox.SandboxedFunction(
    "set_selinux_module.py",
    read_write_paths=["/etc"],
    capabilities=["CAP_DAC_OVERRIDE"],
)


def enable_container_userns(currently_enabled: bool) -> int:
    """Enable container-domain user namespace creation."""
    if currently_enabled:
        print("Container-domain user namespace creation is already enabled.")
        return 0
    print_wrapped(f"""
        Container-domain user namespace creation (e.g. for distrobox) is currently
        disabled. Enabling it now by disabling SELinux module '{CONTAINER_USERNS_MODULE}'.
    """)
    exit_code = sandbox.run(semodule_function, "disable", CONTAINER_USERNS_MODULE)
    if exit_code == 0:
        print("Container-domain user namespace creation enabled.")
    return exit_code


def disable_container_userns(currently_enabled: bool, *, prompt: bool = True) -> int:
    """Disable container-domain user namespace creation."""
    if not currently_enabled:
        print("Container-domain user namespace creation is already disabled.")
        return 0
    print_wrapped(f"""
        Container-domain user namespace creation (e.g. for bubblejail) is currently
        enabled. Disabling it now by enabling SELinux module '{CONTAINER_USERNS_MODULE}'.
    """)
    try:
        proceed = stop_containers(prompt=prompt)
    except subprocess.CalledProcessError:
        print("Failed to stop containers. Aborting...")
        return 1
    if not proceed:
        print("Aborting...")
        return 0
    exit_code = sandbox.run(semodule_function, "enable", CONTAINER_USERNS_MODULE)
    if exit_code == 0:
        print("Container-domain user namespace creation disabled.")
    return exit_code


def run(mode: ToggleMode, *, prompt: bool = True) -> int:
    """Run the logic for enabling or disabling container-domain userns."""
    if mode == ToggleMode.HELP:
        print(HELP_MESSAGE)
        return 0
    userns_enabled = container_userns_enabled()
    match mode:
        case ToggleMode.STATUS:
            print("enabled" if userns_enabled else "disabled")
            return 0
        case ToggleMode.ON:
            return enable_container_userns(userns_enabled)
        case ToggleMode.OFF:
            return disable_container_userns(userns_enabled, prompt=prompt)
        case _:
            raise ValueError(f"Invalid mode value: {mode}")


def main() -> int:
    """Handle the arguments and run the script."""
    try:
        mode = parse_basic_toggle_args(
            prompt="Would you like container-domain user namespace creation to be enabled?"
        )
    except CommandUsageError as e:
        print(f"Usage error: {e}. See usage with --help.")
        return 2

    return run(mode)


if __name__ == "__main__":
    sys.exit(main())
