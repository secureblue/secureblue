#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Privileged inner script to install Dangerzone.
"""

import configparser
import json
from typing import Final

CONTAINERS_POLICY_PATH: Final[str] = "/etc/containers/policy.json"
DZ_CONTAINER_PATH: Final[str] = "/usr/share/dangerzone/container.tar"
DZ_REPO_PATH: Final[str] = "/etc/yum.repos.d/dangerzone.repo"


def enable_repo(path: str | bytes, name: str) -> None:
    """Enable RPM repository"""
    config = configparser.ConfigParser()
    config.read(path)
    if config[name].get("enabled") == "1":
        return
    config[name]["enabled"] = "1"
    with open(path, "w", encoding="utf8") as f:
        config.write(f)


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
    print("Setting container policy to allow Dangerzone...")
    set_container_policy()


if __name__ == "__main__":
    main()
