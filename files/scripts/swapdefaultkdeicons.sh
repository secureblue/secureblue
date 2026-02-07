#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0


# sets default/pinned applications on the taskmanager applet on the panel, there is no nice way to do this
# https://bugs.kde.org/show_bug.cgi?id=511560
sed -i 's/\<applications:org\.kde\.discover\.desktop\>/applications:io.github.kolunmi.Bazaar.desktop/g' /usr/share/plasma/plasmoids/org.kde.plasma.taskmanager/contents/config/main.xml
