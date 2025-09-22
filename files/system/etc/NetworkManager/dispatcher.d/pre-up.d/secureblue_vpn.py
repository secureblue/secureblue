#!/usr/bin/env python3

"""
A NetworkManager dispatcher that runs before every VPN connection.

If the connection is new (i.e. not in CONNECTIONS_FILE), it applies the
key=value pairs in the [vpn] section of DEFAULTS_FILE to the connection using
nmcli.
"""

# Subprocess calls are all made to nmcli as an absolute path using trusted
# inputs. Where inputs are read from DEFAULTS_FILE, we check permissions to make
# sure the file is only writable by root first.
import os
import subprocess  # nosec
import sys
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path
from stat import S_IMODE
from typing import Final

CONFIG_SECTION: Final[str] = "vpn"
CONNECTIONS_FILE: Final[Path] = Path("/etc/NetworkManager/sb-connections.conf")
DEFAULTS_FILE: Final[Path] = Path("/etc/NetworkManager/sb-connection-defaults.conf")
DISPATCHER_ACTION: Final[str] = "pre-up"
MAXIMUM_DEFAULTS_FILE_PERM: Final[int] = 0o0644
REQUIRED_ARGV_COUNT: Final[int] = 3
VPN_TYPES: Final[list[str]] = ["vpn", "wireguard"]


@dataclass(frozen=True)
class NMConnection:
    """
    A NetworkManager connection.

    Attributes:
    nm_interface: str -- the `ip link` interface (e.g. proton0, wlp1s0).
    nm_id: str -- the human-readable connection name.
    nm_uuid: str -- the UUID assigned by NM.
    nm_type: str -- the connection.type assigned by NM, e.g. "wireguard", "802-11-wireless".
    """

    nm_interface: str
    nm_id: str
    nm_uuid: str
    nm_type: str

    def is_already_processed(self) -> bool:
        """Returns True if connection is already listed in CONNECTIONS_FILE, otherwise False."""

        if not CONNECTIONS_FILE.exists():
            return False

        with CONNECTIONS_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                line_uuid = line.split("#", 1)[0].strip()
                if line_uuid == self.nm_uuid:
                    return True
        return False

    def apply_settings(self, settings: dict[str, str]) -> None:
        """Applies the key-value pairs in the settings dictionary to this connection."""

        for key, value in settings.items():
            # nosemgrep: dangerous-subprocess-use-audit
            nm_proc = subprocess.run(  # nosec
                ["/usr/bin/nmcli", "connection", "modify", "uuid", self.nm_uuid, key, value],
                check=False,
                text=True,
                capture_output=True,
            )
            if nm_proc.returncode:
                print(
                    f'Failed to set "{key}" = "{value}" on connection "{self.nm_uuid}".',
                    file=sys.stderr,
                )
                print(nm_proc.stderr, file=sys.stderr)
                # Don't quit just because a single setting fails.
                # Sometimes we have to try applying ipv6.dns to an ipv6=disabled
                # VPN, which throws an error.
            print(f'Set "{key}" = "{value}" on connection "{self.nm_uuid}".')

        self._mark_processed()
        self._reapply_to_interfaces()

    def _mark_processed(self) -> None:
        """Marks the connection as processed by adding its UUID to CONNECTIONS_FILE."""

        if not CONNECTIONS_FILE.exists():
            # Don't let all users see connections they might not have a right to see.
            CONNECTIONS_FILE.touch(mode=0o0600)

        with CONNECTIONS_FILE.open("a", encoding="utf-8") as f:
            if self.nm_id:
                f.write(f"{self.nm_uuid} # {self.nm_id}\n")
            else:
                f.write(f"{self.nm_uuid}\n")

    def _reapply_to_interfaces(self) -> None:
        """Reapply this connection's settings to its interface."""

        # nosemgrep: dangerous-subprocess-use-audit
        nm_proc = subprocess.run(  # nosec
            ["/usr/bin/nmcli", "device", "reapply", self.nm_interface],
            check=False,
            text=True,
            capture_output=True,
        )
        if nm_proc.returncode:
            print(
                f"Failed to reapply connection to interface {self.nm_interface}.", file=sys.stderr
            )
            print(nm_proc.stderr, file=sys.stderr)
            sys.exit(nm_proc.returncode)
        print(f"Reapplied settings to interface {self.nm_interface}.")

    @classmethod
    def from_environment(cls) -> "NMConnection":
        """Creates an NMConnection from the dispatcher environment variables and argv."""

        if len(sys.argv) != REQUIRED_ARGV_COUNT:
            print(
                f"Invalid number of arguments: expected {REQUIRED_ARGV_COUNT}, ",
                "got {len(sys.argv)}.",
                file=sys.stderr,
            )
            sys.exit(1)

        nm_action = sys.argv[2]
        if nm_action != DISPATCHER_ACTION:
            print(
                f"Invoked with incorrect action: expected {DISPATCHER_ACTION}, got {nm_action}.",
                file=sys.stderr,
            )
            sys.exit(1)

        nm_id = os.getenv("CONNECTION_ID")
        nm_uuid = os.getenv("CONNECTION_UUID")
        if not nm_id or not nm_uuid:
            print(
                "Expected environment variables: CONNECTION_ID, CONNECTION_UUID.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Disregards CONNECTION_EXTERNAL: typically a dispatcher would ignore
        # externally-managed connections, but even these VPN connections might
        # need tampering with.

        # nosemgrep: dangerous-subprocess-use-audit
        nm_proc = subprocess.run(  # nosec
            ["/usr/bin/nmcli", "-g", "connection.type", "connection", "show", "uuid", nm_uuid],
            check=False,
            text=True,
            capture_output=True,
        )
        if nm_proc.returncode:
            print(f"Unable to get type for connection {nm_id}.", file=sys.stderr)
            print(nm_proc.stderr, file=sys.stderr)
            sys.exit(nm_proc.returncode)
        nm_type = nm_proc.stdout.strip()

        return cls(sys.argv[1], nm_id, nm_uuid, nm_type)


def defaults_from_file() -> dict[str, str]:
    """Produces a key-value dictionary of the settings in DEFAULTS_FILE."""

    if not DEFAULTS_FILE.exists(follow_symlinks=False):
        print(
            f"{DEFAULTS_FILE.as_posix()} does not exist, no defaults to apply.",
            file=sys.stderr,
        )
        sys.exit(0)

    # DEFAULTS_FILE is applied to all connections, we consider it trusted input
    # so make sure it is only writable by root.
    defaults_stat = DEFAULTS_FILE.stat(follow_symlinks=False)
    if (
        DEFAULTS_FILE.is_symlink()
        or defaults_stat.st_uid != 0
        or defaults_stat.st_gid != 0
        or S_IMODE(defaults_stat.st_mode) > MAXIMUM_DEFAULTS_FILE_PERM
    ):
        print(
            f"Inappropriate permissions on {DEFAULTS_FILE.as_posix()}: ",
            "expected real file owned by root:root with permissions <=0644.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Not a TOCTOU if only root can chmod/chown/write and not a symlink.
    parser = ConfigParser(strict=True)
    parser.optionxform = str
    parser.read(DEFAULTS_FILE.as_posix(), encoding="utf-8")
    if not parser.has_section(CONFIG_SECTION):
        print(f"Expected [vpn] section in {DEFAULTS_FILE.as_posix()}. Exiting.", file=sys.stderr)
        sys.exit(0)

    return dict(parser.items(CONFIG_SECTION))


def main() -> None:
    """Apply the defaults from DEFAULTS_FILE to the connection given to this dispatcher."""
    connection = NMConnection.from_environment()
    if connection.nm_type not in VPN_TYPES:
        print(f"Dispatcher not running for type {connection.nm_type}.", file=sys.stderr)
        return
    if connection.is_already_processed():
        print(
            f'Connection "{connection.nm_id}" has already had defaults applied. No action.',
            file=sys.stderr,
        )
        return

    connection.apply_settings(defaults_from_file())


if __name__ == "__main__":
    main()
