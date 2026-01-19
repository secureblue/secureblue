# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Enable or disable Homebrew installation
[positional-arguments]
set-brew *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/brew_main.py "$@"

# Toggle libvirt daemons on or off
[positional-arguments]
set-libvirt-daemons *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/set_libvirt_daemons.py "$@"

# Enable or disable Xwayland
[positional-arguments]
set-xwayland *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/set_xwayland.py "$@"
