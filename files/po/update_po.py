#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Run this script to update POT and PO files to reflect source code changes.
"""

import glob
import json
import os
import subprocess
import sys
from typing import Final

COPYRIGHT_HEADER: Final[str] = """\
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0
"""

DEFAULT_COPYRIGHT_HEADER: Final[str] = """\
# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the PACKAGE package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
"""

SOURCE_FILES_PATH: Final[str] = "files/po/po-source-files.json"


def command_stdout(*args: str) -> str:
    """Run a command in the shell and return the contents of stdout."""
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


os.chdir(os.path.dirname(sys.argv[0]))
git_root = command_stdout("git", "rev-parse", "--show-toplevel")
os.chdir(git_root)

with open(SOURCE_FILES_PATH, encoding="utf8") as f:
    domain_map = json.load(f)

# This is the locale used for translatable strings in the repo.
# `msginit` requires this to be set to work properly.
os.environ["LANG"] = "en_US.UTF-8"

for domain, source_files in domain_map.items():
    pot_path = f"files/po/{domain}.pot"
    pot_contents = command_stdout("xgettext", "-d", domain, "-o", "-", *source_files)
    pot_contents = pot_contents.replace(DEFAULT_COPYRIGHT_HEADER, COPYRIGHT_HEADER, 1)
    if not pot_contents.endswith("\n"):
        pot_contents += "\n"
    with open(pot_path, "w", encoding="utf8") as f:
        f.write(pot_contents)

    for po_path in glob.iglob(f"files/po/*/{glob.escape(domain)}.po"):
        if po_path.startswith("files/po/en/"):
            subprocess.run(
                ["msginit", "-i", pot_path, "-o", po_path, "--no-translator"], check=True
            )
        else:
            subprocess.run(["msgmerge", "--backup=none", "--update", po_path, pot_path], check=True)
