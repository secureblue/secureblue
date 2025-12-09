#!/usr/bin/python3

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Enable, disable, or check status of container-domain user namespace creation."""

import subprocess  # nosec
import sys
from typing import Final

import sandbox
from utils import ToggleMode, ask_yes_no, command_succeeds, print_wrapped

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
    """Stop all containers and shut down podman."""
    if prompt:
        print("Warning: This will stop ALL containers and shut down podman.")
        if not ask_yes_no("Are you sure you want to do this?"):
            return False
    print("Stopping all containers and shutting down podman...")
    subprocess.run(["/usr/bin/podman", "stop", "--all"], check=True)  # nosec
    subprocess.run(["/usr/bin/killall", "catatonit"], check=False)  # nosec
    print_wrapped("""
        Warning: If catatonit is running as root, you may need to reboot your
        machine to reset podman state.
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
    userns_enabled = container_userns_enabled()
    match mode:
        case "status":
            print("enabled" if userns_enabled else "disabled")
            return 0
        case "on":
            return enable_container_userns(userns_enabled)
        case "off":
            return disable_container_userns(userns_enabled, prompt=prompt)
        case _:
            raise ValueError(f"Invalid mode '{mode}'")


def main() -> int:
    """Handle the arguments and run the script."""

    argc_interactive = 1
    argc_on_off = 2

    if len(sys.argv) == argc_interactive:
        # Ask interactively.
        mode = (
            "on"
            if ask_yes_no("Would you like container-domain user namespace creation to be enabled?")
            else "off"
        )
    elif len(sys.argv) == argc_on_off:
        # Take mode from first argument, i.e. 'on' or 'off'.
        mode = sys.argv[1].casefold()
    else:
        print("Too many options specified, see usage with --help.", file=sys.stderr)
        return 2

    if mode in ("help", "-h", "--help"):
        print(HELP_MESSAGE)
        return 0

    try:
        mode = ToggleMode(mode)
    except ValueError:
        print("Invalid option selected. Try --help.")
        return 2

    return run(mode)


if __name__ == "__main__":
    sys.exit(main())
