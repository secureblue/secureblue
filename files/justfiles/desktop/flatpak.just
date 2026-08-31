# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Add or remove the unfiltered Flathub remote.
[positional-arguments]
@set-flathub-unfiltered *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/set_flathub_unfiltered.py "$@"

# Harden flatpaks by preloading hardened_malloc (highest supported hwcap). When called with a flatpak application ID as an argument, applies the overrides to that application instead of globally.
[positional-arguments]
@harden-flatpak *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/harden_flatpak.py "$@"

# Harden Flatpaks further by rejecting dangerous permissions.
@flatpak-permissions-lockdown:
    exec /usr/bin/python3 /usr/libexec/secureblue/flatpak_perms_lockdown.py

# Resets Flatpak's global overrides
flatpak-reset-global-overrides:
    #!/usr/bin/bash
    GLOBAL_OVERRIDES="${HOME}/.local/share/flatpak/overrides/global"
    echo "This will undo the harden-flatpak command, the flatpak-permissions-lockdown command, as well as any other global overrides (individual app overrides will not be affected)."
    echo "It will not delete the file, but simply move it from ${GLOBAL_OVERRIDES} to ${GLOBAL_OVERRIDES}.save"
    mv "${GLOBAL_OVERRIDES}" "${GLOBAL_OVERRIDES}.save"
