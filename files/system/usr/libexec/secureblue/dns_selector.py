#!/usr/bin/python3

"""Sets DNS configuration, a.k.a. `ujust dns-selector`."""

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

import configparser
import ipaddress
import json
import sys
import textwrap
from argparse import ArgumentParser
from pathlib import Path
from typing import Final
from urllib.parse import urlparse

import sandbox
from sandbox import SandboxedFunction

DNSCONFD_CONF_FILE: Final[Path] = Path("/etc/dnsconfd.conf")
NM_GLOBALDNS_CONF_FILE: Final[Path] = Path("/etc/NetworkManager/conf.d/global-dns.conf")
TRIVALENT_POLICY_FILE: Final[Path] = Path(
    "/etc/trivalent/policies/managed/10-securedns-browser.json"
)
SERVERS_JSON_FILE: Final[Path] = Path("/usr/share/secureblue/secure-dns-providers.json")

dns_function = SandboxedFunction("dns.py", read_write_paths=["/etc"])


def ask_option(options_count: int) -> int:
    """Returns the user's chosen number between 1 and options_count: int from STDIN."""

    while True:
        raw_option = interruptible_ask(f"Choose an option [1-{options_count}]: ")
        if raw_option.isdigit():
            option = int(raw_option)
            if 1 <= option <= options_count:
                print()
                return option
        print(f"Please enter a number between 1 and {options_count}.")


def ask_yes_no(prompt: str) -> bool:
    """Returns the user's preference between 'yes'/'y' (True) and 'no'/'n' (False)."""

    while True:
        ans = interruptible_ask(prompt + " [y/n] ").casefold()
        if ans in ("y", "yes", "n", "no"):
            return ans in ("y", "yes")
        print("Please enter y (yes) or n (no).")


def ask_should_use_doh() -> bool:
    """Returns the user's preference for Trivalent DoH enforcement (yes = true, no = false)."""

    print(
        textwrap.dedent(
            """
            Would you like to enable DNS over HTTPS (DoH) in the Trivalent browser?
            This tool already configures encrypted DNS over TLS, but DoH looks like HTTPS
            traffic to outsiders, which could have privacy benefits.
            1. Enable DoH for Trivalent (masks DNS queries);
            2. Use the same encrypted DNS as the rest of the system in Trivalent.
            """
        ).strip()
    )
    option = ask_option(2)
    return option == 1


def ask_should_validate_dnssec() -> bool:
    """Returns the user's preference for local DNSSEC validation (yes = true, no = false)."""

    print(
        textwrap.dedent(
            """
            Would you like to enable DNSSEC validation?
            1. Yes (most secure): Use the Internet's 'root zone' trust anchors to check all
               DNS responses. The servers suggested by this tool will work, but some default
               or custom servers give 'bogus' results that cause resolution to fail.
            2. No (less secure, more compatible): Trust your chosen DNS server to validate
               for you. If you use a default or insecure DNS server, you will not be
               protected from forged responses. This is needed for some public WiFi networks
               to redirect you to their captive portal.
            """
        ).strip()
    )
    option = ask_option(2)
    return option == 1


def ask_nm_servers() -> tuple[str, str]:
    """
    Get user to choose DNS servers from SERVERS_JSON_FILE as a numbered option from STDIN.

    Returns tuple[
        nm_servers: str, -- a comma-delimited list of DNS servers in NetworkManager format.
        https_endpoint: str -- a validated HTTPS URL for use as a DoH endpoint.
    ]
    """

    data = json.loads(SERVERS_JSON_FILE.read_text(encoding="utf-8"))
    providers = data["providers"]

    print("Select a DNS provider:")
    custom_option = len(providers) + 1
    for i, p in enumerate(providers, start=1):
        print(f"{i}. {p.get('providerName')}: {p.get('providerDescription')}")
    print(f"{custom_option}. Choose custom DNS resolvers")

    provider_selection = ask_option(len(providers) + 1)
    if provider_selection == custom_option:
        return ask_custom_nm_servers()
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
    nm_servers = ",".join([*server.get("ipv4", []), *server.get("ipv6", [])])
    https_endpoint = server.get("https")
    return (nm_servers, https_endpoint)


def run_interactive() -> int:
    """
    Prompt to (1) reset, (2) set global DNS, DNSSEC and Trivalent DoT, or (3) set DNSSEC only.
    """

    print(
        textwrap.dedent(
            """
            Would you like to:
            1. Reset global DNS to automatic mode (likely insecure);
            2. Enforce secure DNS servers for all connections (can cause VPN DNS leaks
               or break local services, but allows for DoH in stealth/censorship scenarios);
            3. Toggle local DNSSEC validation.
            4. Print current DNS status.
            """
        ).strip()
    )
    mode = ask_option(4)

    match mode:
        case 1:
            # Reset.
            return sandbox.run(dns_function, "reset")

        case 2:
            # Enforce globally.
            nm_servers, https_endpoint = ask_nm_servers()
            should_validate_dnssec = "true" if ask_should_validate_dnssec() else "false"
            if https_endpoint and not ask_should_use_doh():
                https_endpoint = ""
            return sandbox.run(
                dns_function, "set-global", nm_servers, should_validate_dnssec, https_endpoint
            )

        case 3:
            # Toggle DNSSEC.
            should_validate_dnssec = "true" if ask_should_validate_dnssec() else "false"
            return sandbox.run(dns_function, "set-dnssec", should_validate_dnssec)

        case 4:
            # Print status.
            # Successful exits of run_interactive() lead to a print_all_status() in main().
            return 0

        case _:
            return 1


def print_dnssec_status() -> None:
    """Print DNSSEC status to STDOUT, i.e. 'DNSSEC: <enabled|disabled>'."""
    try:
        dnssec_enabled = False
        with DNSCONFD_CONF_FILE.open("r", encoding="utf-8") as f:
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
        print("DNSSEC: unable to open and parse configuration")


def print_nm_globaldns_status() -> None:
    """
    Print global DNS enablement status and indented server list to STDOUT.

    For example:
    Global DNS: <enabled|disabled>
    Global DNS servers:
        dns+tls://1.2.3.4#host
        dns+tls://[::1]#host
    """
    nm_parser = configparser.ConfigParser(strict=False, delimiters=("=",))
    nm_parser.optionxform = str
    nm_parser.read(NM_GLOBALDNS_CONF_FILE.as_posix())

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
    Print Trivalent DNS over HTTPS enablement status and endpoint to STDOUT.

    For example:
    Trivalent DoH: <enabled|disabled>
    Trivalent DoH endpoint: https://host/endpoint
    """
    try:
        with TRIVALENT_POLICY_FILE.open("r", encoding="utf-8") as f:
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
        print("Trivalent DoH: configuration invalid")
    except (OSError, UnicodeDecodeError):
        print("Trivalent DoH: unable to open and parse configuration")


def interruptible_ask(prompt: str) -> str:
    """Get a string input from STDIN, strip whitespace, and exit gracefully on SIGINT."""
    try:
        return input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(130)


def ask_valid_ipv4(prompt: str) -> str:
    """Returns a valid IPv4 address as a string."""
    while True:
        ip = interruptible_ask(prompt)
        try:
            ipaddress.IPv4Address(ip)
            return ip
        except ValueError:
            print("Invalid IPv4 address, try again.")


def ask_valid_ipv6(prompt: str) -> str:
    """Returns a valid IPv6 address enclosed in square brackets as a string."""
    while True:
        ip = interruptible_ask(prompt).strip(" []")
        try:
            ipaddress.IPv6Address(ip)
            return f"[{ip}]"
        except ValueError:
            print("Invalid IPv6 address, try again.")


def ask_valid_https(prompt: str) -> str:
    """Returns a valid HTTPS URL."""
    while True:
        raw_url = interruptible_ask(prompt)
        if not raw_url:  # Allow empty.
            return ""
        url = urlparse(raw_url)
        if url.scheme == "https" and url.netloc:
            print()
            return raw_url
        print("Invalid HTTPS endpoint, try again.")


def ask_custom_nm_servers() -> tuple[str, str]:
    """
    Get valid primary (+/- secondary) IPv4 (+/- IPv6) global DNS servers from STDIN.

    Returns tuple[
        nm_servers: str, -- a comma-delimited list of DNS servers in NetworkManager format.
        https_endpoint: str -- a validated HTTPS URL for use as a DoH endpoint.
    ]
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

    hostname = ""
    has_hostname = ask_yes_no(
        "Does the resolver provide a TLS hostname/SNI to verify its authenticity?\n"
        "(e.g. cloudflare-dns.com)"
    )
    if has_hostname:
        hostname = interruptible_ask("Enter the resolver's TLS hostname/SNI: ")

    https_endpoint = ""
    has_https_endpoint = ask_yes_no(
        "Does the resolver provide a DNS over HTTPS URL?\n"
        "(e.g. https://cloudflare-dns.com/dns-query)"
    )
    if has_https_endpoint:
        https_endpoint = ask_valid_https("Enter the resolver's DoH URL:")

    tokens = []
    for ip in (ipv4_primary, ipv4_secondary, ipv6_primary, ipv6_secondary):
        if ip:
            tokens.append(f"dns+tls://{ip}#{hostname}" if hostname else f"dns+tls://{ip}")
    nm_servers = ",".join(tokens)
    print()
    return nm_servers, https_endpoint


def print_all_status() -> None:
    """Prints report on global DNS status, servers, DNSSEC and Trivalent DoH status to STDOUT."""

    print_nm_globaldns_status()
    print_dnssec_status()
    print_trivalent_doh_status()


def main() -> int:
    """
    Sets DNS configuration.

    ujust dns-selector -- Interactive.
    ujust dns-selector reset
    ujust dns-selector dnssec <on|off>
    ujust dns-selector status
    """

    p = ArgumentParser(
        prog="ujust dns-selector", description="Sets global DoT servers, DNSSEC and Trivalent DoH."
    )
    cmd_p = p.add_subparsers(dest="cmd", required=False)
    cmd_p.add_parser("reset", help="Resets all settings to default/automatic.")
    cmd_p.add_parser(
        "status",
        help="Reads status from config files. Lists active servers and "
        "shows global DNS, DNSSEC and Trivalent DoH enablement.",
    )
    dnssec_p = cmd_p.add_parser("dnssec", help="Sets local DNSSEC validation.")
    dnssec_p.add_argument("state", choices=["on", "off"])
    args = p.parse_args()

    match args.cmd:
        case None:
            exit_code = run_interactive()
            if exit_code == 0:
                print_all_status()
            return exit_code

        case "status":
            print_all_status()
            return 0

        case "dnssec":
            dnssec = "true" if sys.argv[2] == "on" else "false"
            exit_code = sandbox.run(dns_function, "set-dnssec", dnssec)
            if exit_code == 0:
                print_all_status()
            return exit_code

        case "reset":
            exit_code = sandbox.run(dns_function, "reset")
            if exit_code == 0:
                print_all_status()
            return exit_code

        case _:
            print("Invalid option selected. Try --help.", file=sys.stderr)
            return 1


if __name__ == "__main__":
    sys.exit(main())
