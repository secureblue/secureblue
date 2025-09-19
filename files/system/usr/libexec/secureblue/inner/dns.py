#!/usr/bin/python3

"""Sets DNS configuration. Should be run as root."""

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

# We only make fixed subprocess calls to /usr/bin/systemctl.
import json
import subprocess  # nosec
import sys
from pathlib import Path
from typing import Final

DNSCONFD_CONF_FILE: Final[Path] = Path("/etc/dnsconfd.conf")
NM_GLOBALDNS_CONF_FILE: Final[Path] = Path("/etc/NetworkManager/conf.d/global-dns.conf")
TRIVALENT_POLICY_FILE: Final[Path] = Path(
    "/etc/trivalent/policies/managed/10-securedns-browser.json"
)


def restart_stack() -> int:
    """Reset dnsconfd (which manages Unbound) and NetworkManager."""
    try:
        # We're calling system binaries with fixed arguments and no shell.
        # nosemgrep: dangerous-subprocess-use-audit
        subprocess.run(["/usr/bin/systemctl", "restart", "dnsconfd.service"], check=True)  # nosec
        # nosemgrep: dangerous-subprocess-use-audit
        subprocess.run(["/usr/bin/systemctl", "restart", "NetworkManager.service"], check=True)  # nosec
    except subprocess.CalledProcessError:
        return 1
    return 0


def set_global_nm_servers(nm_servers: str) -> None:
    """
    Set NetworkManager global DNS servers.

    nm_servers: str -- servers in the format "dns+tls://1.2.3.4#host,[::1]#host".
    """
    if not nm_servers:
        NM_GLOBALDNS_CONF_FILE.unlink(missing_ok=True)
        return

    nm_globaldns_config = (
        f"[global-dns]\nresolve-mode=exclusive\n\n[global-dns-domain-*]\nservers={nm_servers}\n"
    )
    NM_GLOBALDNS_CONF_FILE.parent.mkdir(parents=True, exist_ok=True)
    NM_GLOBALDNS_CONF_FILE.write_text(nm_globaldns_config, encoding="utf-8")
    NM_GLOBALDNS_CONF_FILE.chmod(0o644)


def set_trivalent_doh_endpoint(https_endpoint: str) -> None:
    """
    Sets Trivalent DNS over HTTPS policy.

    https_endpoint: str -- A valid HTTPS URL as the endpoint.
    """
    if not https_endpoint:
        TRIVALENT_POLICY_FILE.unlink(missing_ok=True)
        return

    trivalent_policy_json: str = (
        json.dumps(
            {"DnsOverHttpsMode": "secure", "DnsOverHttpsTemplates": https_endpoint}, indent=4
        )
        + "\n"
    )
    TRIVALENT_POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRIVALENT_POLICY_FILE.write_text(trivalent_policy_json, encoding="utf-8")
    TRIVALENT_POLICY_FILE.chmod(0o644)


def set_dnssec_enabled(should_validate: bool) -> None:
    """
    Enables/disables local DNSSEC validation by Unbound.

    should_validate: bool -- True to enable validation, False to disable.
    """
    if not should_validate:
        DNSCONFD_CONF_FILE.unlink(missing_ok=True)
        return

    DNSCONFD_CONF_FILE.write_text("dnssec_enabled: yes\n", encoding="utf-8")
    DNSCONFD_CONF_FILE.chmod(0o644)


def main() -> int:
    """
    Sets DNS configuration.

    dns.py reset -- Resets all settings to default/automatic.
    dns.py set-dnssec <true|false>
        Enables or disables local DNSSEC validation respectively.
    dns.py set-global <servers> <dnssec-enabled> [<doh-url>]
        Sets servers where servers is comma-separated,
        servers -- e.g. "dns+tls://1.2.3.4#host,dns+tls://[::1]#host"
        dnssec-enabled -- <true|false>
        doh-url -- a valid HTTPS URL.
    """
    # If this gets more complex, may move to argparse?
    args_min = 2
    args_set_dnssec = 3
    args_set_global_min = 4
    args_set_global_max = 5
    bool_strings = ("true", "false")

    if len(sys.argv) < args_min:
        return 1

    if sys.argv[1] == "reset" and len(sys.argv) == args_min:
        set_global_nm_servers("")
        set_dnssec_enabled(False)
        set_trivalent_doh_endpoint("")
        return restart_stack()

    if (
        sys.argv[1] == "set-dnssec"
        and len(sys.argv) == args_set_dnssec
        and sys.argv[2] in bool_strings
    ):
        set_dnssec_enabled(sys.argv[2] == "true")
        return restart_stack()

    if sys.argv[1] == "set-global" and len(sys.argv) in (args_set_global_min, args_set_global_max):
        should_validate_dnssec = sys.argv[3]
        if should_validate_dnssec not in bool_strings:
            return 1
        nm_servers = sys.argv[2]
        https_endpoint = sys.argv[4] if len(sys.argv) == args_set_global_max else ""

        set_global_nm_servers(nm_servers)
        set_dnssec_enabled(should_validate_dnssec == "true")
        set_trivalent_doh_endpoint(https_endpoint)
        return restart_stack()

    return 1


if __name__ == "__main__":
    sys.exit(main())
