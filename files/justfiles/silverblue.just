# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Toggle Gnome JIT JavaScript for GJS and WebkitGTK (requires session restart)
@toggle-gnome-jit-js:
    exec /usr/bin/run0 /usr/libexec/secureblue/toggle-gnome-jit-js

# Toggle support for using GNOME user extensions
@toggle-gnome-extensions:
    exec /usr/libexec/secureblue/toggle-gnome-extensions
