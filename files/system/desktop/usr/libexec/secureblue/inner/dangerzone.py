#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Privileged inner script to install Dangerzone.
"""

import configparser
from typing import Final

DZ_REPO_PATH: Final[str] = "/etc/yum.repos.d/dangerzone.repo"


def enable_repo(path: str | bytes, name: str) -> None:
    """Enable RPM repository"""
    config = configparser.ConfigParser(delimiters=("=",))
    config.read(path)
    if config[name].get("enabled") == "1":
        return
    config[name]["enabled"] = "1"
    with open(path, "w", encoding="utf8") as f:
        config.write(f)


def main() -> None:
    """Install Dangerzone."""
    print("Enabling Dangerzone repository...")
    enable_repo(DZ_REPO_PATH, "dangerzone")


if __name__ == "__main__":
    main()
