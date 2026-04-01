#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Run this script to check that the vendored GPG keys for RPM repositories match
the GPG keys at the corresponding remote sources.
"""

import json
import os
import subprocess
import sys
from collections.abc import Generator
from typing import Final

REPO_DATA_PATH: Final[str] = "tools/rpm-repo-sources.json"


def command_stdout(*args: str) -> str:
    """Run a command in the shell and return the contents of stdout."""
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.rstrip("\n")


def repo_uses_gpg_key(repo_path: str, key_path: str) -> bool:
    """Check whether RPM repo uses the provided local key path for its GPG key."""
    live_key_path = key_path.removeprefix("files/system")
    live_key_path = live_key_path.removeprefix("/desktop").removeprefix("/nvidia")
    with open(repo_path, encoding="utf8") as f:
        for line in f:
            if not line.startswith("gpgkey"):
                continue
            repo_key_path = line.split("=", maxsplit=1)[1].strip().removeprefix("file://")
            if repo_key_path != live_key_path:
                print(f"\n'{repo_key_path}' != '{live_key_path}'")
                return False
    return True


def local_key_matches_remote_key(key_path: str, key_url: str) -> bool:
    """Check whether local GPG key is identical to remote GPG key at URL."""
    with open(key_path, encoding="utf8") as f:
        local_key = f.read().rstrip("\n")

    remote_key = command_stdout("curl", "-fLsS", "--retry", "5", key_url)
    return local_key == remote_key


def gpg_key_fingerprints(key_path: str) -> Generator[str]:
    """Yield fingerprints of GPG key at given path."""
    # Reference for GPG colon-listing format: https://github.com/gpg/gnupg/blob/master/doc/DETAILS
    gpg_output = command_stdout("gpg", "--show-keys", "--with-colons", key_path)
    for line in gpg_output.splitlines():
        if line.startswith(("fpr:", "fp2:")):
            yield line.split(":")[9]


def local_key_has_fingerprint(key_path: str, fingerprint: str) -> bool:
    """Check whether local GPG key has the specified fingerprint."""
    return any(fingerprint == fpr for fpr in gpg_key_fingerprints(key_path))


def verify_repo_data(repo_path: str, key_path: str, key_url: str, fingerprint: str) -> bool:
    """Verify consistency of RPM repository data."""
    print(f"Checking repository {repo_path}")

    print("Verifying repo file points to specified local GPG key... ", end="")
    if not repo_uses_gpg_key(repo_path=repo_path, key_path=key_path):
        print("FAILED!")
        return False
    print("done.")

    print("Verifying local GPG key matches remote GPG key... ", end="")
    if not local_key_matches_remote_key(key_path=key_path, key_url=key_url):
        print("FAILED!")
        return False
    print("done.")

    print("Verifying GPG key has expected fingerprint... ", end="")
    if not local_key_has_fingerprint(key_path=key_path, fingerprint=fingerprint):
        print("FAILED!")
        return False
    print("done.")

    return True


def main() -> int:
    """Main script entry point."""
    # Set working directory to root of this git repo
    script_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    os.chdir(script_path)
    git_root = command_stdout("git", "rev-parse", "--show-toplevel")
    os.chdir(git_root)

    with open(REPO_DATA_PATH, encoding="utf8") as f:
        repo_data_list = json.load(f)

    success = True
    for repo_data in repo_data_list:
        try:
            success &= verify_repo_data(
                repo_path=repo_data["localRepo"],
                key_path=repo_data["localGpgKey"],
                key_url=repo_data["remoteGpgKey"],
                fingerprint=repo_data["gpgFingerprint"],
            )
        except subprocess.CalledProcessError as err:
            print("*** ERROR ***")
            print(err.stderr, file=sys.stderr)
            success = False
        print()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
