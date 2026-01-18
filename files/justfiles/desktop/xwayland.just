# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Enable or disable Xwayland
[positional-arguments]
set-xwayland *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/set_xwayland.py "$@"
