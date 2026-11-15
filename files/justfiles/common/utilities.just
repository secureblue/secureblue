# vim: set ft=make :
# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Clean up old up unused podman images, volumes, flatpak packages and rpm-ostree content
@clean-system:
    exec /usr/libexec/secureblue/clean-system

# Check for local overrides
@check-local-overrides:
    exec /usr/libexec/secureblue/check-local-overrides

alias assemble := distrobox-assemble

# Create distroboxes from a defined manifest
[positional-arguments]
@distrobox-assemble CONTAINER="prompt" ACTION="create" FILE="/etc/distrobox/distrobox.ini":
    exec /usr/libexec/secureblue/distrobox-assemble "$@"

# Create toolbox containers from a defined manifest (this spec will not be expanded)
[positional-arguments]
@toolbox-assemble CONTAINER="prompt" ACTION="create" FILE="/etc/toolbox/toolbox.ini":
    exec /usr/libexec/secureblue/toolbox-assemble "$@"

# Rebase to a different secureblue Desktop Environment/Atomic Desktop
@rebase-secureblue:
    exec /usr/libexec/secureblue/rebase-secureblue

# Apply SELinux type "user_home_t" on external drives to allow access from Trivalent
@label-external-drives:
    exec /usr/libexec/secureblue/label-external-drives

# Setup USBGuard
@setup-usbguard:
    exec /usr/libexec/secureblue/setup-usbguard
