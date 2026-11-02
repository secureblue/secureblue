# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Add or remove the unfiltered Flathub remote.
[positional-arguments]
@set-flathub-unfiltered *args:
    exec /usr/bin/python3 -Es /usr/libexec/secureblue/set_flathub_unfiltered.py "$@"

# Harden flatpaks by preloading hardened_malloc (highest supported hwcap). When called with a flatpak application ID as an argument, applies the overrides to that application instead of globally.
[positional-arguments]
@harden-flatpak *args:
    exec /usr/bin/python3 -Es /usr/libexec/secureblue/harden_flatpak.py "$@"

# Harden Flatpaks further by disabling all permissions by default and rejecting known arbitrary DBus names, applies only to the current user
@flatpak-permissions-lockdown:
    exec /usr/libexec/secureblue/flatpak-permissions-lockdown

# Resets Flatpak's global overrides
@flatpak-reset-global-overrides:
    exec /usr/libexec/secureblue/flatpak-reset-global-overrides
