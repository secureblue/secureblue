#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap


def command_stdout(*args: str) -> str:
    """Run a command in the shell and return the contents of stdout."""
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.rstrip("\n")


def extract_recipe(raw_recipe: str) -> str:
    """Remove recipe header and dedent script"""
    recipe = "\n".join(line for line in raw_recipe.splitlines() if line.startswith((" ", "\t")))
    return textwrap.dedent(recipe + "\n")


def normalize_shebang(script: str) -> str:
    return re.sub(r"^#!\s*(?:(?:/usr)?/bin/run0\s+)?", "#!", script)


def is_shell_script(script: str) -> bool:
    """Test if string looks like a shell script"""
    matches = re.match(r"#!\s*(?:/usr)?/bin/(?:env\s+)?(?:ba)?sh\s*$", script, flags=re.MULTILINE)
    return matches is not None


script_path = os.path.abspath(os.path.dirname(sys.argv[0]))
os.chdir(script_path)
git_root = command_stdout("git", "rev-parse", "--show-toplevel")
os.chdir(git_root)

justfiles = []
for root, _, files in os.walk("files/justfiles"):
    justfiles += (f"{root}/{file}" for file in files)

print("Running ShellCheck on scripts in the following justfiles:")
print(*justfiles, sep="\n", end="\n\n")

temp_dir = tempfile.mkdtemp(prefix="justfile-tmp-", dir=".")
recipe_paths = []
for justfile in justfiles:
    try:
        recipes = command_stdout("just", "-f", justfile, "--summary").split()
    except subprocess.CalledProcessError:
        print(f"Error parsing justfile '{justfile}'")
        sys.exit(1)
    for recipe in recipes:
        raw_recipe = command_stdout("just", "-f", justfile, "--show", recipe)
        recipe_script = normalize_shebang(extract_recipe(raw_recipe))
        if is_shell_script(recipe_script):
            recipe_fd, recipe_path = tempfile.mkstemp(dir=temp_dir, prefix=f"{recipe}-")
            with open(recipe_fd, "w", encoding="utf8") as recipe_file:
                recipe_file.write(recipe_script)
            recipe_paths.append(recipe_path)

result = subprocess.run(["shellcheck", *sys.argv[1:], "--", *recipe_paths], check=False)

shutil.rmtree(temp_dir)

sys.exit(result.returncode)
