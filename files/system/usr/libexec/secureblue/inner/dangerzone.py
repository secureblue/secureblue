#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Privileged inner script to install Dangerzone.
"""

import configparser
import json
import re
from typing import Final

CONTAINERS_POLICY_PATH: Final[str] = "/etc/containers/policy.json"
DZ_CONTAINER_PATH: Final[str] = "/usr/share/dangerzone/container.tar"
DZ_REPO_PATH: Final[str] = "/etc/yum.repos.d/dangerzone.repo"
PTRACE_CONF_PATH: Final[str] = "/etc/sysctl.d/61-ptrace-scope.conf"


def enable_repo(path: str | bytes, name: str) -> None:
    """Enable RPM repository"""
    config = configparser.ConfigParser()
    config.read(path)
    if config[name].get("enabled") == "1":
        return
    config[name]["enabled"] = "1"
    with open(path, "w", encoding="utf8") as f:
        config.write(f)


def set_ptrace_scope(path: str) -> None:
    """Edit ptrace scope sysctl value in file."""
    new_contents = b""
    pattern = re.compile(rb"^kernel\.yama\.ptrace_scope\s*=\s*3")
    ptrace_scope_line = b"kernel.yama.ptrace_scope = 2\n"
    modified = False
    try:
        with open(path, "rb") as f:
            for line in f:
                if re.match(pattern, line):
                    new_contents += ptrace_scope_line
                    modified = True
                else:
                    new_contents += line
    except FileNotFoundError:
        return
    if modified:
        with open(path, "wb") as f:
            f.write(new_contents)


def set_container_policy() -> None:
    """Allow Dangerzone container archive in policy.json."""
    with open(CONTAINERS_POLICY_PATH, "rb") as f:
        policy = json.load(f)
    if DZ_CONTAINER_PATH in policy["transports"]["oci-archive"]:
        return
    policy["transports"]["oci-archive"][DZ_CONTAINER_PATH] = [{"type": "insecureAcceptAnything"}]
    with open(CONTAINERS_POLICY_PATH, "w", encoding="utf8") as f:
        json.dump(policy, f, indent=2)


def main() -> None:
    """Install Dangerzone."""
    print("Enabling Dangerzone repository...")
    enable_repo(DZ_REPO_PATH, "dangerzone")
    print("Ensuring ptrace is allowed...")
    set_ptrace_scope(PTRACE_CONF_PATH)
    print("Setting container policy to allow Dangerzone...")
    set_container_policy()


if __name__ == "__main__":
    main()
