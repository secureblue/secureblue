# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Enable or disable Homebrew installation
[positional-arguments]
@set-brew *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/brew_main.py "$@"

# Enable or disable Xwayland
[positional-arguments]
@set-xwayland *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/set_xwayland.py "$@"

# Enable Dangerzone (sandboxed PDF sanitizer)
[positional-arguments]
@enable-dangerzone:
    exec /usr/bin/python3 /usr/libexec/secureblue/enable_dangerzone.py "$@"
