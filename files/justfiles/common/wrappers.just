# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Audit secureblue
[positional-arguments]
audit-secureblue *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/audit_secureblue.py "$@"

# Run a non-flatpak application with standard memory allocator
[no-cd]
[positional-arguments]
with-standard-malloc *args:
    #!/bin/sh
    LD_PRELOAD='' exec "$@"

# Sets bluetooth kernel modules on/off (requires reboot)
[positional-arguments]
set-bluetooth-modules *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/bluetooth_main.py "$@"

# Interactively select secure DNS servers
[positional-arguments]
dns-selector *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/dns_selector.py "$@"

# Add additional boot parameters for hardening (requires reboot)
set-kargs-hardening:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/set_kargs_hardening.py

# Remove all hardening boot parameters (requires reboot)
remove-kargs-hardening:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/remove_kargs_hardening.py

# Sets Brew enabled/disabled
[positional-arguments]
set-brew *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/brew_main.py "$@"

# Create the admin user and remove wheel from the normal user
[positional-arguments]
create-admin *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/create_admin.py "$@"

# Enable, disable, or check status of unconfined-domain user namespace creation.
[positional-arguments]
set-unconfined-userns *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/set_unconfined_userns.py "$@"

# Enable, disable, or check status of container-domain user namespace creation.
[positional-arguments]
set-container-userns *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/set_container_userns.py "$@"

# Install Dangerzone (sandboxed PDF sanitizer)
[positional-arguments]
install-dangerzone:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/install_dangerzone.py "$@"
