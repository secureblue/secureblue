#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Unset LD_PRELOAD in all invocations of systemsettings in .desktop files
sed -Ei 's/^Exec=systemsettings( .*)?$/Exec=with-standard-malloc systemsettings\1/' /usr/share/applications/*.desktop

# Unset LD_PRELOAD for ibus-ui-gtk3 in .desktop file
sed -i 's/^Exec=/Exec=with-standard-malloc /' /usr/share/applications/org.freedesktop.IBus.Panel.Wayland.Gtk3.desktop
