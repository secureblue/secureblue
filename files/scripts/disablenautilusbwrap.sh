#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

sed -i -e 's|^Exec=|Exec=/usr/bin/env SNAP_NAME=nautilus |' \
    /usr/share/applications/org.gnome.Nautilus.desktop \
    /usr/share/dbus-1/services/org.gnome.Nautilus.service \
    /usr/share/dbus-1/services/org.freedesktop.FileManager1.service