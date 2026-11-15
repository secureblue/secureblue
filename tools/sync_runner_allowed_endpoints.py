#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Run this script to sync the list of egress endpoints allowed by
step-security/harden-runner in GitHub Actions runners.

This takes the list of allowed endpoints in POLICY_FILE, and, for each file in
WORKFLOW_FILES, replaces the text between the START_LINE and END_LINE markers
with the policy text from the file, appropriately indented.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Final

POLICY_FILE: Final[Path] = Path(".github/workflows/runner-allowed-endpoints.txt")
WORKFLOW_FILES: Final[list[Path]] = [
    Path(".github/workflows/build-one-recipe.yml"),
    Path(".github/workflows/build-sealed-image.yml"),
    Path(".github/workflows/pr_build.yml"),
]
START_LINE: Final[str] = "##### BEGIN ALLOWED ENDPOINT LIST #####"
END_LINE: Final[str] = "##### END ALLOWED ENDPOINT LIST #####"


def command_stdout(*args: str) -> str:
    """Run a command in the shell and return the contents of stdout."""
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.rstrip("\n")


script_path = os.path.abspath(os.path.dirname(sys.argv[0]))
os.chdir(script_path)
git_root = command_stdout("git", "rev-parse", "--show-toplevel")
os.chdir(git_root)

endpoint_list = POLICY_FILE.read_text()
indentation_pattern = re.compile(r"^([ \t]*)" + START_LINE, re.MULTILINE)

for workflow_file in WORKFLOW_FILES:
    old_workflow_text = workflow_file.read_text()
    m = indentation_pattern.search(old_workflow_text)
    if m is None:
        print(f"Warning: Allowed endpoint list not found in {workflow_file}")
        continue
    indentation = m.group(1)
    start_index = old_workflow_text.index("\n" + indentation + START_LINE + "\n") + 1
    end_index = (
        old_workflow_text.index("\n" + indentation + END_LINE + "\n", start_index)
        + len(indentation)
        + len(END_LINE)
        + 1
    )
    indented_endpoint_list = "\n".join(
        indentation + line if line else "" for line in endpoint_list.splitlines()
    )
    new_workflow_text = (
        old_workflow_text[:start_index] + indented_endpoint_list + old_workflow_text[end_index:]
    )
    workflow_file.write_text(new_workflow_text)
