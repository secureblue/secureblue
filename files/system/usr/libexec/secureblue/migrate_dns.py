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

"""
Idempotent migration and cleanup of resolved config (only that created by
`ujust dns-selector`) to the NetworkManager global-dns format.
Started and sandboxed directly by systemd as secureblue-migrate-dns.service.
"""

import configparser
import os
import pwd
from pathlib import Path
from typing import Final

RESOLVED_SECUREDNS_PATH: Final[Path] = Path("/etc/systemd/resolved.conf.d/10-securedns.conf")
NM_GLOBALDNS_PATH: Final[Path] = Path("/etc/NetworkManager/conf.d/global-dns.conf")
DNSCONFD_PATH: Final[Path] = Path("/etc/dnsconfd.conf")
RESOLVCONF_PATH: Final[Path] = Path("/etc/resolv.conf")


def read_from_resolved() -> tuple[list[str], bool]:
    """
    Returns existing systemd-resolved configuration in NetworkManager format.
    (NetworkManager-style DNS servers, is_dnssec_enabled)
    """
    parser = configparser.ConfigParser(strict=False, delimiters=("=",))
    parser.optionxform = str
    if not parser.read(RESOLVED_SECUREDNS_PATH) or "Resolve" not in parser:
        return [], False

    resolve = parser["Resolve"]

    dot_value = (resolve.get("DNSOverTLS") or "").casefold().strip()
    dnssec_value = (resolve.get("DNSSEC") or "").casefold().strip()
    is_tls_enabled = dot_value in ("true", "yes")
    is_dnssec_enabled = dnssec_value in ("true", "yes")

    nm_servers = []
    dns_line = (resolve.get("DNS") or "").strip()

    if not dns_line:
        return [], False

    for token in dns_line.split():
        server = token.split("#", 1)
        ip = server[0].strip()
        hostname = server[1].strip() if len(server) > 1 else ""

        if ":" in ip:
            ip = f"[{ip.strip('[]')}]"  # Clean IPv6.

        nm_server = ""
        if is_tls_enabled:
            nm_server = "dns+tls://" + ip
            nm_server += ("#" + hostname) if hostname else ""
        else:
            nm_server = ip

        nm_servers.append(nm_server)

    return nm_servers, is_dnssec_enabled


def write_to_nm(nm_servers: list[str], is_dnssec_enabled: bool) -> None:
    """
    Writes NetworkManager-style DNS servers to NM_GLOBALDNS_PATH, and the DNSSEC
    enablement status to DNSCONFD_PATH, which manages unbound config.
    Overwrites. Deletes if there is no effective configuration.
    """
    NM_GLOBALDNS_PATH.parent.mkdir(parents=True, exist_ok=True)  # conf.d.

    # Currently, this aggressively overwrites dnsconfd config.
    if is_dnssec_enabled:
        DNSCONFD_PATH.write_text("dnssec_enabled: yes\n", encoding="utf-8")
        DNSCONFD_PATH.chmod(0o644)
        print(f"Enabled DNSSEC in {DNSCONFD_PATH}")
    else:
        DNSCONFD_PATH.unlink(missing_ok=True)
        print(f"DNSSEC not set, clearing {DNSCONFD_PATH}")

    if not nm_servers:
        print("securedns.conf seems empty. Making no further changes to global DNS configuration.")
        return

    nm_globaldns_config = (
        "[global-dns]\n"
        "resolve-mode=exclusive\n\n"
        "[global-dns-domain-*]\n"
        f"servers={','.join(nm_servers)}\n"
    )
    NM_GLOBALDNS_PATH.write_text(nm_globaldns_config, encoding="utf-8")
    NM_GLOBALDNS_PATH.chmod(0o644)
    print(f"Set DNS in {NM_GLOBALDNS_PATH} to {','.join(nm_servers)}")


def main() -> None:
    """Remove stub resolv.conf and migrate resolved 10-globaldns.conf to NetworkManager."""

    if RESOLVCONF_PATH.exists(follow_symlinks=False) and RESOLVCONF_PATH.is_symlink():
        print(f"{RESOLVCONF_PATH.as_posix()} is a symlink!")
        RESOLVCONF_PATH.unlink()
        RESOLVCONF_PATH.touch()
        RESOLVCONF_PATH.chmod(0o644)
        dnsconfd_uid = pwd.getpwnam("dnsconfd").pw_uid
        # Default behavior is to leave root as group.
        os.chown(RESOLVCONF_PATH, uid=dnsconfd_uid, gid=0)
        print(f"{RESOLVCONF_PATH.as_posix()} is now a real file owned by dnsconfd:root.")

    if not RESOLVED_SECUREDNS_PATH.exists():
        print("No secureblue resolved DNS configuration found. Not migrating.")
        return

    print("Migrating secureblue DNS from resolved to NetworkManager.")

    (nm_servers, is_dnssec_enabled) = read_from_resolved()
    write_to_nm(nm_servers, is_dnssec_enabled)
    RESOLVED_SECUREDNS_PATH.unlink()

    print("Finished migrating secureblue DNS to NetworkManager.")


if __name__ == "__main__":
    main()
