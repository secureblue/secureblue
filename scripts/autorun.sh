#!/usr/bin/env bash

# Tell this script to exit if there are any errors.
set -oue pipefail

#
# AUTORUN:
#
# This script simplifies your "recipe.yml" management whenever you simply want
# to "run everything automatically" based on whatever script files exist on disk.
#
# Set any or all of your "recipe.yml" script categories to "autorun.sh", and
# enjoy the magic! The autorunner will then automatically look up all ".sh"
# script files within the corresponding "scripts/<script mode>/" directory,
# executing them all in their correct alphabetical and numerical filename order.
#
# For example, if you've assigned "autorun.sh" to the "scripts.pre" category
# of your "recipe.yml", then it will scan and automatically execute everything
# in your "scripts/pre/" directory.
#
# There are a few rules, which aim to simplify your script management:
#
# - It will only execute scripts at the FIRST level within the directory, which
#   means that anything stored in "scripts/pre/deeperfolder/" will NOT execute.
#   This is intentional, so that you can store libraries and helper scripts
#   within subdirectories, to simplify your script organization.
#
# - You script directories and the scripts within them can be symlinks, to allow
#   easy reuse of scripts. For example, if you want the same scripts to execute
#   during both the "pre" and "post" stages, you could simply symlink individual
#   scripts or the entire "pre" and "post" directories to each other. However,
#   remember to only use RELATIVE symlinks, to ensure that the links work
#   properly. For example, "ln -s ../pre/foo.sh scripts/post/foo.sh".
#
# - The scripts will be executed with the name of the current "build execution
#   phase" as their first and only argument, to allow you to easily reuse scripts
#   across multiple stages. This is consistent with the "build.sh" behavior.
#
# - All scripts execute in a numerically and alphabetically sorted order, which
#   allows you to easily control the execution order of your scripts. If it's
#   important that they execute in a specific order, then you should give them
#   appropriate names. For example, "05-foo.sh" would always execute before
#   another script named "99-bar.sh". It's recommended to use zero-padded,
#   numerical prefixes when you want to specify the execution order.
#
# - It's possible to mix your "autorun scripts" with your regular "recipe.yml"
#   scripts. The autorunner will only execute things from the correctly named
#   sub-directories. And the manually listed "recipe.yml" scripts should simply
#   be stored directly within "scripts/", or in a custom sub-directory that
#   doesn't match any of the "script category" names. For example, you could
#   set the "scripts.pre" category of "recipe.yml" to execute both "autorun.sh"
#   and "fizzwidget/something.sh", and then place a bunch of auto-executed
#   scripts under "scripts/pre/" for the autorunner. This makes it very simple
#   to reuse common scripts between multiple different "recipe.yml" files,
#   by just placing all commonly shared scripts within auto-runner folders,
#   and then manually listing a few specific per-"recipe.yml" scripts within
#   each recipe that needs some extra customizations.
#
# - You can safely specify this autorun script as your runner in "recipe.yml",
#   even if the corresponding directory doesn't exist or doesn't contain any
#   scripts. It will gracefully skip the processing if there's nothing to do.
#

# Helper functions.
yell() { echo "${0}: ${*}"; }
abort() { yell "${*}"; exit 0; }
die() { yell "${*}"; exit 1; }

# Determine which directory and script category we're executing under.
SCRIPT_DIR="$(dirname -- "${BASH_SOURCE[0]}")"
SCRIPT_MODE="${1:-}"
if [[ -z "${SCRIPT_MODE}" ]]; then
    die "Missing script mode argument."
fi

# Ensure that a "scripts/" sub-directory exists for the "script category".
# Note that symlinks to other directories will be accepted by the `-d` check.
RUN_DIR="${SCRIPT_DIR}/${SCRIPT_MODE}"
if [[ ! -d "${RUN_DIR}" ]]; then
    abort "Nothing to do, since \"${RUN_DIR}\" doesn't exist."
fi

# Generate a numerically sorted array of all scripts (or symlinks to scripts),
# without traversing into deeper subdirectories (to allow the user to store
# helper libraries in subfolders without accidental execution). Sorting is
# necessary for manually controlling the execution order via numeric prefixes.
mapfile -t buildscripts < <(find -L "${RUN_DIR}" -maxdepth 1 -type f -name "*.sh" | sort -n)

# Exit if there aren't any scripts in the directory.
if [[ ${#buildscripts[@]} -eq 0 ]]; then
    abort "Nothing to do, since \"${RUN_DIR}\" doesn't contain any scripts in its top-level directory."
fi

# Now simply execute all of the discovered scripts, and provide the name of the
# current "script category" as an argument, to match the behavior of "build.sh".
for script in "${buildscripts[@]}"; do
    echo "[autorun.sh] Running [${SCRIPT_MODE}]: ${script}"
    "$script" "${SCRIPT_MODE}"
done
