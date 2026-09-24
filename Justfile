# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

@_default:
    just --list

# Compare vendered RPM repo GPG keys to remote GPG keys
check-repo-keys:
    exec tools/check_repo_keys.py

# Run ShellCheck on shell scripts embedded in justfiles
shellcheck-justfiles:
    exec tools/shellcheck_justfiles.py

# Build systemd sysext from this repo's version of /usr
[group('sysext')]
build-sysext:
    exec tools/build-sysext.sh

# Install sysext, immediately applying this repo's version of /usr to the running system
[confirm("Caution: This applies this repo's version of /usr directly to your system.\nOnly do this on a trusted branch.\nProceed? [y/N]")]
[group('sysext')]
install-sysext: build-sysext
    run0 --via-shell tools/install-sysext.sh

# Remove sysext, restoring the system's /usr to its original state
[group('sysext')]
remove-sysext:
    run0 --via-shell tools/remove-sysext.sh
