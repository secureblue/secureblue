#!/usr/bin/python3

"""Sets DNS configuration. Should be run as root."""

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# We only make fixed subprocess calls to /usr/bin/systemctl.
import argparse
import json
import os
import pwd
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from enum import Enum
from functools import partialmethod
from pathlib import Path
from typing import Final

DNSCONFD_CONF_PATH: Final[Path] = Path("/etc/dnsconfd.conf")
DNSCONFD_MANAGER_PATH: Final[Path] = Path("/etc/NetworkManager/conf.d/dnsconfd.conf")
NM_GLOBALDNS_CONF_PATH: Final[Path] = Path("/etc/NetworkManager/conf.d/global-dns.conf")
RESOLVCONF_PATH: Final[Path] = Path("/etc/resolv.conf")
RESOLVED_RESOLVCONF_PATH: Final[Path] = Path("/run/systemd/resolve/stub-resolv.conf")
TRIVALENT_POLICY_PATH: Final[Path] = Path(
    "/etc/trivalent/policies/managed/10-securedns-browser.json"
)


@dataclass(frozen=True)
class SystemdService:
    """
    A systemd service.

    Attributes:
        name (str): The unit name, e.g. "dnsconfd.service".
    """

    name: str

    def _do_systemctl_action(self, *actions: str) -> None:
        """
        Perform an action on a systemd service. Retry and eventually log on failure.

        Args:
            action (str): systemctl action (e.g. "start")
        """
        # nosemgrep: dangerous-subprocess-use-audit
        systemctl = subprocess.run(
            ["/usr/bin/systemctl", *actions, self.name], check=False, capture_output=True
        )

        if not systemctl.returncode:
            # All good.
            return

        # Error, so wait a few seconds and try again.
        time.sleep(3)
        # nosemgrep: dangerous-subprocess-use-audit
        systemctl = subprocess.run(
            ["/usr/bin/systemctl", *actions, self.name], check=False, stdout=subprocess.PIPE
        )

        if systemctl.returncode:
            print(f"Failed to {' '.join(actions)} {self.name}.", file=sys.stderr)
            sys.exit(systemctl.returncode)

    disable = partialmethod(_do_systemctl_action, "disable")
    disable_now = partialmethod(_do_systemctl_action, "disable", "--now")
    enable = partialmethod(_do_systemctl_action, "enable")
    enable_now = partialmethod(_do_systemctl_action, "enable", "--now")
    stop = partialmethod(_do_systemctl_action, "stop")
    start = partialmethod(_do_systemctl_action, "start")
    mask = partialmethod(_do_systemctl_action, "mask")
    unmask = partialmethod(_do_systemctl_action, "unmask")

    def is_enabled(self) -> bool:
        """Returns whether the systemd service is enabled."""
        # nosemgrep: dangerous-subprocess-use-audit
        systemctl = subprocess.run(
            ["/usr/bin/systemctl", "is-enabled", "--quiet", self.name],
            check=False,
            capture_output=True,
        )
        return not systemctl.returncode


class DNSResolver(Enum):
    """A DNS resolver, such as Unbound or systemd-resolved."""

    UNBOUND = "dnsconfd.service"
    RESOLVED = "systemd-resolved.service"

    @property
    def service(self) -> SystemdService:
        """Gets the systemd service associated with this resolver."""
        return SystemdService(self.value)

    @classmethod
    def get_current(cls) -> "DNSResolver":
        """
        Gets the resolver whose systemd service is enabled.

        Warns and returns `DNSResolver.UNBOUND` if an unsupported configuration is detected.
        """

        unbound_enabled = cls.UNBOUND.service.is_enabled()
        resolved_enabled = cls.RESOLVED.service.is_enabled()

        if unbound_enabled and resolved_enabled:
            print(
                "Warning: multiple DNS resolvers are enabled.\n"
                "Continuing anyway. You may need to restart your device after this change.",
                file=sys.stderr,
            )
            return cls.UNBOUND

        if not unbound_enabled and not resolved_enabled:
            print(
                "Warning: dnsconfd.service and systemd-resolved.service are disabled.\n"
                "Continuing anyway. You may need to restart your device after this change.",
                file=sys.stderr,
            )
            return cls.UNBOUND

        return cls.UNBOUND if unbound_enabled else cls.RESOLVED


def set_resolver(resolver: DNSResolver) -> None:
    """
    Sets the DNS resolver (e.g. dnsconfd-unbound, systemd-resolved) to use.

    Args:
        resolver (DNSResolver): The DNS resolver to use.
    """

    match resolver:
        case DNSResolver.UNBOUND:
            DNSResolver.RESOLVED.service.mask()
            DNSResolver.RESOLVED.service.disable()

            # NetworkManager needs to be told to use dnsconfd.
            DNSCONFD_MANAGER_PATH.write_text("[main]\ndns=dnsconfd\n", encoding="utf-8")
            DNSCONFD_MANAGER_PATH.chmod(0o644)
            # resolv.conf needs to be a real file owned by dnsconfd:root.
            RESOLVCONF_PATH.unlink(missing_ok=True)
            RESOLVCONF_PATH.touch()  # Cannot set mode here because of umask.
            RESOLVCONF_PATH.chmod(0o644)
            dnsconfd_uid = pwd.getpwnam("dnsconfd").pw_uid  # For unprivileged dnsconfd.
            os.chown(RESOLVCONF_PATH, uid=dnsconfd_uid, gid=0)  # gid 0 is default behavior.

            SystemdService("unbound.socket").enable_now()
            SystemdService("unbound-control.socket").enable_now()
            DNSResolver.UNBOUND.service.unmask()
            DNSResolver.UNBOUND.service.enable()

        case DNSResolver.RESOLVED:
            DNSResolver.UNBOUND.service.disable()
            DNSResolver.UNBOUND.service.mask()
            SystemdService("unbound.socket").disable_now()
            SystemdService("unbound-control.socket").disable_now()

            DNSCONFD_MANAGER_PATH.unlink(missing_ok=True)
            # systemd-resolved is implicitly detected by NetworkManager based on
            # a resolv.conf symlink.
            RESOLVCONF_PATH.unlink(missing_ok=True)
            RESOLVCONF_PATH.symlink_to(RESOLVED_RESOLVCONF_PATH.as_posix())

            DNSResolver.RESOLVED.service.unmask()
            DNSResolver.RESOLVED.service.enable()


def set_global_nm_servers(servers: str | None = None) -> None:
    """
    Set NetworkManager global DNS servers.

    Args:
        nm_servers (str): servers in the format "dns+tls://1.2.3.4#host,[::1]#host".
    """
    if not servers:
        NM_GLOBALDNS_CONF_PATH.unlink(missing_ok=True)
        return

    nm_globaldns_config = textwrap.dedent(
        f"""
        [global-dns]
        resolve-mode=exclusive

        [global-dns-domain-*]
        servers={servers}
        """
    ).strip()
    NM_GLOBALDNS_CONF_PATH.parent.mkdir(parents=True, exist_ok=True)
    NM_GLOBALDNS_CONF_PATH.write_text(f"{nm_globaldns_config}\n", encoding="utf-8")
    NM_GLOBALDNS_CONF_PATH.chmod(0o644)


def set_trivalent_doh_endpoint(https_endpoint: str | None = None) -> None:
    """
    Sets Trivalent DNS over HTTPS policy.

    Args:
        https_endpoint (str): A valid HTTPS URL as the endpoint.
    """
    if not https_endpoint:
        TRIVALENT_POLICY_PATH.unlink(missing_ok=True)
        return

    trivalent_policy_json = json.dumps(
        {"DnsOverHttpsMode": "secure", "DnsOverHttpsTemplates": https_endpoint}, indent=4
    )
    TRIVALENT_POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRIVALENT_POLICY_PATH.write_text(f"{trivalent_policy_json}\n", encoding="utf-8")
    TRIVALENT_POLICY_PATH.chmod(0o644)


def set_dnssec_enabled(should_validate: bool) -> None:
    """
    Enables/disables local DNSSEC validation by Unbound.

    Args:
        should_validate (bool): True to enable validation, False to disable.
    """
    if not should_validate:
        DNSCONFD_CONF_PATH.unlink(missing_ok=True)
        return

    DNSCONFD_CONF_PATH.write_text("dnssec_enabled: yes\n", encoding="utf-8")
    DNSCONFD_CONF_PATH.chmod(0o644)


def parse_args() -> argparse.Namespace:
    """Parse command-line inputs."""

    p = argparse.ArgumentParser(prog="dns.py", description="Sets DNS configuration.")
    cmd_p = p.add_subparsers(dest="cmd", required=True)
    cmd_p.add_parser("reset", help="Reset all settings to defaults.")

    dnssec_p = cmd_p.add_parser("set-dnssec", help="Enable or disable DNSSEC.")
    dnssec_p.add_argument(
        "dnssec_enabled",
        help="'true' to enable DNSSEC, 'false' to disable.",
        choices=["true", "false"],
    )

    global_p = cmd_p.add_parser("set-global", help="Set global DNS.")
    global_p.add_argument("servers", help="Comma-separated list of NetworkManager DNS servers.")
    global_p.add_argument(
        "dnssec_enabled",
        help="'true' to enable DNSSEC, 'false' to disable.",
        choices=["true", "false"],
    )
    global_p.add_argument("doh_url", nargs="?", help="Valid HTTPS URL for DoH.")

    resolver_p = cmd_p.add_parser("set-resolver", help="Change the stub resolver.")
    resolver_p.add_argument(
        "resolver",
        help="'unbound' for dnsconfd-unbound, 'resolved' for systemd-resolved.",
        choices=["unbound", "resolved"],
    )

    doh_p = cmd_p.add_parser("set-trivalent-doh", help="Toggle Trivalent DoH.")
    doh_p.add_argument("doh_url", help="Valid HTTPS URL.")

    return p.parse_args()


def main() -> None:
    """Configure DNS according to command-line arguments."""

    args = parse_args()

    if args.cmd == "set-trivalent-doh":
        # Do this early because we don't need to bring down the network stack.
        set_trivalent_doh_endpoint(args.doh_url)
        print("Configured DNS over HTTPS in Trivalent only.")
        return

    # Stop everything.
    print("Configuring DNS. Your connection will be reset. Please wait.")
    nm = SystemdService("NetworkManager.service")
    nm.stop()
    DNSResolver.get_current().service.stop()
    time.sleep(2)

    match args.cmd:
        case "reset":
            set_resolver(DNSResolver.UNBOUND)
            set_global_nm_servers(None)
            set_dnssec_enabled(False)
            set_trivalent_doh_endpoint(None)

        case "set-dnssec":
            set_resolver(DNSResolver.UNBOUND)
            set_dnssec_enabled(args.dnssec_enabled == "true")

        case "set-global":
            # Only support global DNS for Unbound. The purpose of allowing
            # rollback to resolved is that VPN clients want to push dynamic
            # DNS configuration to it (e.g. depending on connection state). If
            # global DNS were acceptable, the user could still use Unbound.
            if DNSResolver.get_current() != DNSResolver.UNBOUND:
                print("Global DNS is only supported with Unbound.", file=sys.stderr)
                return

            set_global_nm_servers(args.servers)
            set_dnssec_enabled(args.dnssec_enabled == "true")
            set_trivalent_doh_endpoint(args.doh_url)

        case "set-resolver":
            set_global_nm_servers(None)
            set_dnssec_enabled(False)
            if args.resolver == "resolved":
                set_resolver(DNSResolver.RESOLVED)
            else:
                set_resolver(DNSResolver.UNBOUND)

        case _:
            print("Invalid option selected. Try --help.", file=sys.stderr)
            sys.exit(1)

    time.sleep(2)
    DNSResolver.get_current().service.start()
    nm.start()


if __name__ == "__main__":
    main()
