# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Enable, disable, or check status of SSH password authentication
[positional-arguments]
set-ssh-password-auth *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/set_ssh_password_auth.py "$@"
