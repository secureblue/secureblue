#!/usr/bin/python3

"""Sets DNS configuration, a.k.a. `ujust dns-selector`."""

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import configparser
import ipaddress
import json
import sys
import textwrap
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Final
from urllib.parse import urlparse

import sandbox
from sandbox import SandboxedFunction
from utils import ask_option, ask_yes_no, interruptible_ask

RESET: Final[str] = "\033[0m"
BOLD: Final[str] = "\033[1m"
DNSCONFD_CONF_PATH: Final[Path] = Path("/etc/dnsconfd.conf")
NM_GLOBALDNS_CONF_PATH: Final[Path] = Path("/etc/NetworkManager/conf.d/global-dns.conf")
RESOLVCONF_PATH: Final[Path] = Path("/etc/resolv.conf")
TRIVALENT_POLICY_PATH: Final[Path] = Path(
    "/etc/trivalent/policies/managed/10-securedns-browser.json"
)
SERVERS_JSON_PATH: Final[Path] = Path("/usr/share/secureblue/secure-dns-providers.json")

dns_function = SandboxedFunction(
    "dns.py",
    read_write_paths=["/etc"],
    capabilities=["CAP_SYS_ADMIN", "CAP_DAC_OVERRIDE", "CAP_CHOWN", "CAP_FOWNER"],
    additional_sandbox_properties=["--property=SystemCallFilter=@chown", "--background="],
)


def ask_should_use_doh() -> bool:
    """Returns the user's preference for Trivalent DoH enforcement (yes = True, no = False)."""
    print(
        textwrap.dedent(
            f"""
            Would you like to enable DNS over HTTPS (DoH) in the Trivalent browser?
            {BOLD}1. Enable:{RESET}  Send Trivalent's DNS queries to your chosen HTTPS endpoint.
            {BOLD}2. Disable:{RESET} Use the same encrypted DNS as the rest of the system.
            """
        ).strip()
    )
    option = ask_option(2)
    return option == 1


def ask_should_validate_dnssec() -> bool:
    """Returns the user's preference for local DNSSEC validation (yes = True, no = False)."""

    print(
        textwrap.dedent(
            f"""
            Would you like to enable local DNSSEC validation?
            {BOLD}1. Enable:{RESET}  Validate your chosen server's responses for all signed domains.
               Uses the Internet's "root trust anchors" for zero-trust lookups.
            {BOLD}2. Disable:{RESET} Trust your chosen nameserver to validate DNSSEC for you.
               Our suggested servers validate DNSSEC, but custom providers may not.
            """
        ).strip()
    )
    option = ask_option(2)
    return option == 1


@dataclass(frozen=True)
class DNSServers:
    """A DNS server to be set as a global upstream by NetworkManager."""

    servers_csv: str | None
    https_endpoint: str | None


def _ask_custom_ips() -> str:
    """
    Returns a comma-separated list of IPs and protocols representing the user's custom servers.

    Example output:
        `dns+tls://1.1.1.1#domain.com,dns+tls://[::1]#domain.com,dns+udp://2.2.2.2`
    """

    ipv4_primary = ask_valid_ipv4("Enter the resolver's IPv4 address (e.g. 1.1.1.1): ")
    ipv4_secondary = ""
    has_secondary = ask_yes_no("Does the resolver provide a second IPv4 address?")
    if has_secondary:
        ipv4_secondary = ask_valid_ipv4("Enter the secondary IPv4 address: ")

    ipv6_primary = ipv6_secondary = ""
    has_ipv6 = ask_yes_no("Does the resolver support IPv6 (e.g. 2620:fe::fe)?")
    if has_ipv6:
        ipv6_primary = ask_valid_ipv6("Enter the resolver's IPv6 address: ")
        if has_secondary:
            ipv6_secondary = ask_valid_ipv6("Enter the resolver's second IPv6 address: ")

    hostname = None
    has_dot = ask_yes_no(
        "Does the resolver provide a TLS hostname/SNI to verify its authenticity?\n"
        "(e.g. cloudflare-dns.com)"
    )
    if has_dot:
        hostname = interruptible_ask("Enter the resolver's TLS hostname/SNI: ")

    tokens = []
    for ip in (ipv4_primary, ipv4_secondary, ipv6_primary, ipv6_secondary):
        if ip:
            tokens.append(f"dns+tls://{ip}#{hostname}" if hostname else f"dns+tls://{ip}")
    return ",".join(tokens)


def ask_custom_servers(https_only: bool) -> DNSServers:
    """
    Ask for valid primary (+/- secondary) IPv4 (+/- IPv6) global DNS servers.

    Args
        https_only (bool): Whether to ask only for a DoH URL. In this case,
        DNSServers is returned with servers_csv = None.
    """

    servers_csv = None if https_only else _ask_custom_ips()

    https_endpoint = None
    has_https_endpoint = https_only or ask_yes_no(
        "Does the resolver provide a DNS over HTTPS URL?\n"
        "(e.g. https://cloudflare-dns.com/dns-query)"
    )
    if has_https_endpoint:
        https_endpoint = ask_valid_https("Enter the resolver's DoH URL: ")

    return DNSServers(servers_csv, https_endpoint)


def ask_servers(https_only: bool = False) -> DNSServers:
    """
    Ask user to choose a DNS server, either from SERVERS_JSON_FILE or custom.

    Args
        https_only (bool): Whether to only prompt for a HTTPS endpoint if needed.
    """

    data = json.loads(SERVERS_JSON_PATH.read_text(encoding="utf-8"))
    providers = data["providers"]

    print("Select a DNS provider:")
    custom_option = len(providers) + 1
    for i, p in enumerate(providers, start=1):
        print(f"{BOLD}{i}. {p.get('providerName')}:{RESET} {p.get('providerDescription')}")
    print(f"{BOLD}{custom_option}.{RESET} Choose custom DNS resolvers")

    provider_selection = ask_option(len(providers) + 1)
    if provider_selection == custom_option:
        return ask_custom_servers(https_only)
    provider = providers[provider_selection - 1]

    servers = provider["servers"]
    if len(servers) > 1:
        print(f"Select server profile for {provider.get('providerName')}:")
        for i, s in enumerate(servers, start=1):
            print(f"{i}. {s.get('serverDescription')}")
        server_selection = ask_option(len(servers))
    else:
        server_selection = 1

    server = servers[server_selection - 1]
    servers_csv = ",".join([*server.get("ipv4", []), *server.get("ipv6", [])])
    https_endpoint = server.get("https")
    return DNSServers(servers_csv, https_endpoint)


class DNSResolver(Enum):
    """A DNS resolver."""

    UNBOUND = auto()
    RESOLVED = auto()
    UNKNOWN = auto()

    @classmethod
    def detect(cls) -> "DNSResolver":
        """Returns the current resolver based on the contents of /etc/resolv.conf."""
        # Unlike in dns.py, the exact services running are unimportant, as we
        # need to be VPN aware and measure the effective configuration.
        try:
            with open(RESOLVCONF_PATH, encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if line.startswith("nameserver"):
                        _, addr, *_ = line.split()
                        if addr == "127.0.0.1":
                            return cls.UNBOUND
                        if addr == "127.0.0.53":
                            return cls.RESOLVED
            return cls.UNKNOWN

        except (OSError, UnicodeDecodeError):
            print("Unable to open and parse /etc/resolv.conf.", file=sys.stderr)
            return cls.UNKNOWN


def ask_resolver() -> DNSResolver:
    """Asks for the user's choice of resolver."""
    print(
        textwrap.dedent(
            f"""
            Which DNS resolver would you like to use?
            {BOLD}1. Unbound:{RESET}  Cache and prefetch DNS records for performance.
               Typically more reliable and supports local DNSSEC validation.
            {BOLD}2. resolved:{RESET} Use the Fedora default, systemd-resolved.
               Better compatibility with some VPNs.
            """
        ).strip()
    )
    option = ask_option(2)
    return DNSResolver.UNBOUND if option == 1 else DNSResolver.RESOLVED


def run_interactive() -> int:
    """Interactive menu with the same functions as `ujust dns-selector --help`."""
    print(f"{BOLD}Current status:{RESET}")
    print_all_status()
    print()

    print(
        textwrap.dedent(
            f"""
            What DNS settings would you like to modify?
            Press Ctrl+C to exit the script at any stage.
            {BOLD}1. Reset to defaults.{RESET}
               Uses the Unbound resolver with DNSSEC disabled.
            {BOLD}2. Configure DNS over HTTPS in Trivalent.{RESET}
               Masks your DNS queries as regular HTTPS requests when web browsing.
            """
        ).strip()
    )
    if DNSResolver.detect() != DNSResolver.UNBOUND:
        mode = ask_option(2)
    else:
        print(
            textwrap.dedent(
                f"""
                {BOLD}3. Configure DNSSEC.{RESET}
                   Toggle local validation, to allow/block spoofed responses.
                {BOLD}4. Configure global DNS.{RESET}
                   Enforce secure DNS for all connections, including VPNs.
                {BOLD}5. Change the resolver.{RESET}
                   Switch from Unbound (usually more reliable, supports DNSSEC) to
                   systemd-resolved for better compatibility with some VPNs.
                """
            ).strip()
        )
        mode = ask_option(5)

    exit_code = 1
    match mode:
        case 1:
            # Reset to defaults.
            exit_code = sandbox.run(dns_function, "reset")

        case 2:
            # Trivalent DoH.
            use_doh = ask_should_use_doh()
            server = ask_servers(https_only=True).https_endpoint if use_doh else ""
            exit_code = sandbox.run(dns_function, "set-trivalent-doh", server)

        case 3:
            # Configure DNSSEC.
            should_validate_dnssec = "true" if ask_should_validate_dnssec() else "false"
            exit_code = sandbox.run(dns_function, "set-dnssec", should_validate_dnssec)

        case 4:
            # Configure global DNS. Unbound only.
            servers = ask_servers()
            should_validate_dnssec = "true" if ask_should_validate_dnssec() else "false"
            https_endpoint = (
                servers.https_endpoint
                if servers.https_endpoint is not None and ask_should_use_doh()
                else ""
            )
            exit_code = sandbox.run(
                dns_function,
                "set-global",
                servers.servers_csv,
                should_validate_dnssec,
                https_endpoint,
            )

        case 5:
            # Switch to systemd-resolved.
            exit_code = sandbox.run(dns_function, "set-resolver", "resolved")

    print(f"\n{BOLD}Finished configuring DNS.{RESET}")
    return exit_code


def print_current_resolver() -> None:
    """
    Prints current DNS resolver.

    Example:
        DNS Resolver: Unbound|systemd-resolved|unknown/vpn
    """
    match DNSResolver.detect():
        case DNSResolver.UNBOUND:
            print("DNS Resolver: Unbound")
        case DNSResolver.RESOLVED:
            print("DNS Resolver: systemd-resolved")
        case _:
            print("DNS Resolver: unknown/vpn")


def print_dnssec_status() -> None:
    """
    Print DNSSEC status.

    Example:
        DNSSEC: enabled|disabled
    """
    if DNSResolver.detect() != DNSResolver.UNBOUND:
        print("DNSSEC: unavailable")
        return

    try:
        dnssec_enabled = False
        with DNSCONFD_CONF_PATH.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("dnssec_enabled:"):
                    [_, value] = line.split(":", 1)
                    dnssec_enabled = value.strip().casefold() in ("yes", "true")
                    # Don't break as there may be a contradictory line later.
        print("DNSSEC: enabled" if dnssec_enabled else "DNSSEC: disabled")
    except FileNotFoundError:
        print("DNSSEC: disabled")
    except (OSError, UnicodeDecodeError):
        print("DNSSEC: unable to open and parse configuration", file=sys.stderr)


def print_nm_globaldns_status() -> None:
    """
    Print global DNS enablement status and indented server list to STDOUT.

    Example:
        Global DNS: enabled|disabled

        Global DNS servers:
            dns+tls://1.2.3.4#host
            dns+tls://[::1]#host
    """
    if DNSResolver.detect() != DNSResolver.UNBOUND:
        print("Global DNS: unavailable")
        return

    nm_parser = configparser.ConfigParser(strict=False, delimiters=("=",))
    nm_parser.optionxform = str
    nm_parser.read(NM_GLOBALDNS_CONF_PATH.as_posix())

    if not nm_parser.has_section("global-dns"):
        print("Global DNS: disabled")
        return

    resolve_mode = nm_parser["global-dns"].get("resolve-mode")
    resolve_status = "enabled" if resolve_mode == "exclusive" else "disabled"
    print(f"Global DNS: {resolve_status}")

    if nm_parser.has_section("global-dns-domain-*"):
        servers = nm_parser["global-dns-domain-*"].get("servers", "")
        if servers:
            print("Global DNS servers:")
            for server in servers.split(","):
                print(f"  {server}")


def print_trivalent_doh_status() -> None:
    """
    Print Trivalent DNS over HTTPS enablement status and endpoint.

    Example:
        Trivalent DoH: enabled|disabled
        Trivalent DoH endpoint: https://host/endpoint
    """
    try:
        with TRIVALENT_POLICY_PATH.open("r", encoding="utf-8") as f:
            policy = json.load(f)
            doh_mode = policy.get("DnsOverHttpsMode")
            doh_endpoint = policy.get("DnsOverHttpsTemplates")
            doh_status = "enabled" if doh_mode == "secure" and doh_endpoint else "disabled"
            print(f"Trivalent DoH: {doh_status}")
            if doh_endpoint:
                print(f"Trivalent DoH endpoint: {doh_endpoint}")
    except FileNotFoundError:
        print("Trivalent DoH: disabled")
    except json.JSONDecodeError:
        print("Trivalent DoH: configuration invalid", file=sys.stderr)
    except (OSError, UnicodeDecodeError):
        print("Trivalent DoH: unable to open and parse configuration", file=sys.stderr)


def ask_valid_ipv4(prompt: str) -> str:
    """Returns a valid IPv4 address."""
    while True:
        ip = interruptible_ask(prompt)
        try:
            ipaddress.IPv4Address(ip)
            return ip
        except ValueError:
            print("Invalid IPv4 address, try again.")


def ask_valid_ipv6(prompt: str) -> str:
    """Returns a valid IPv6 address enclosed in square brackets."""
    while True:
        ip = interruptible_ask(prompt).strip(" []")
        try:
            ipaddress.IPv6Address(ip)
            return f"[{ip}]"
        except ValueError:
            print("Invalid IPv6 address, try again.")


def ask_valid_https(prompt: str) -> str | None:
    """Returns a valid HTTPS URL."""
    while True:
        raw_url = interruptible_ask(prompt)
        if not raw_url:  # Allow empty.
            return None
        url = urlparse(raw_url)
        if url.scheme == "https" and url.netloc:
            print()
            return raw_url
        print("Invalid HTTPS endpoint, try again.")


def print_all_status() -> None:
    """Prints the entire DNS state tracked by `ujust dns-selector` for audit."""

    print_current_resolver()
    print_dnssec_status()
    print_nm_globaldns_status()
    print_trivalent_doh_status()


def parse_args() -> argparse.Namespace:
    """Parse command-line input to `ujust dns-selector`. Doesn't expose Global DNS."""

    p = argparse.ArgumentParser(
        prog="ujust dns-selector", description="Sets global DoT servers, DNSSEC and Trivalent DoH."
    )

    cmd_p = p.add_subparsers(dest="cmd", required=False)
    cmd_p.add_parser("reset", help="Resets all settings to default/automatic.")
    cmd_p.add_parser("status", help="Reads status from config files.")

    dnssec_p = cmd_p.add_parser("dnssec", help="Sets local DNSSEC validation.")
    dnssec_p.add_argument("enable_dnssec", choices=["on", "off"])

    unbound_p = cmd_p.add_parser("resolver", help="Sets which DNS resolver is used.")
    unbound_p.add_argument("backend", choices=["unbound", "resolved"])

    args = p.parse_args()
    if args.cmd == "resolver":
        if args.backend == "unbound":
            args.backend = DNSResolver.UNBOUND
        else:
            args.backend = DNSResolver.RESOLVED
    if args.cmd == "dnssec":
        args.enable_dnssec = args.enable_dnssec == "on"

    return args


def main() -> int:
    """
    Sets DNS configuration.

    Examples:
        $ ujust dns-selector
        $ ujust dns-selector reset
        $ ujust dns-selector dnssec <on|off>
        $ ujust dns-selector resolver <unbound|resolved>
        $ ujust dns-selector status
    """
    args = parse_args()

    exit_code = 0
    match args.cmd:
        case None:
            exit_code = run_interactive()

        case "status":
            pass

        case "dnssec":
            if DNSResolver.detect() != DNSResolver.UNBOUND:
                print("DNSSEC unavailable with current resolver.", file=sys.stderr)
                return 1
            dnssec = "true" if args.enable_dnssec else "false"
            exit_code = sandbox.run(dns_function, "set-dnssec", dnssec)

        case "reset":
            exit_code = sandbox.run(dns_function, "reset")

        case "resolver":
            resolver = "unbound" if args.backend == DNSResolver.UNBOUND else "resolved"
            exit_code = sandbox.run(dns_function, "set-resolver", resolver)

        case _:
            print("Invalid option selected. Try --help.", file=sys.stderr)
            return 1

    print_all_status()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
