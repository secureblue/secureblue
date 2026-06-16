# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Audit secureblue
[positional-arguments]
@audit-secureblue *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/audit_secureblue.py "$@"

# Run a non-flatpak application with standard memory allocator
[no-cd]
[no-exit-message]
[positional-arguments]
@with-standard-malloc *args:
    exec /usr/bin/with-standard-malloc "$@"

# Sets bluetooth kernel modules on/off (requires reboot)
[positional-arguments]
@set-bluetooth-modules *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/bluetooth_main.py "$@"

# Enable or disable CUPS (the printing service).
[positional-arguments]
@set-cups *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/set_cups.py "$@"

# Sets webcam kernel modules on/off (requires reboot)
[positional-arguments]
@set-webcam-modules *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/webcam_main.py "$@"

# Interactively select secure DNS servers
[positional-arguments]
@dns-selector *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/dns_selector.py "$@"

# Add additional boot parameters for hardening (requires reboot)
@set-kargs-hardening:
    exec /usr/bin/python3 /usr/libexec/secureblue/set_kargs_hardening.py

# Remove all hardening boot parameters (requires reboot)
@remove-kargs-hardening:
    exec /usr/bin/python3 /usr/libexec/secureblue/remove_kargs_hardening.py

# Create the admin user and remove wheel from the normal user
[positional-arguments]
@create-admin *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/create_admin.py "$@"

# Enable, disable, or check status of unconfined-domain user namespace creation.
[positional-arguments]
@set-unconfined-userns *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/set_unconfined_userns.py "$@"

# Enable, disable, or check status of container-domain user namespace creation.
[positional-arguments]
@set-container-userns *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/set_container_userns.py "$@"

# Install Dangerzone (sandboxed PDF sanitizer)
[positional-arguments]
@install-dangerzone:
    exec /usr/bin/python3 /usr/libexec/secureblue/install_dangerzone.py "$@"

# Toggle display of the user-motd in terminal
@toggle-user-motd:
    exec /usr/bin/python3 /usr/libexec/secureblue/toggle_user_motd.py

# Toggle DHCP hostname sending.
[positional-arguments]
@set-dhcp-hostname-sending *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/dhcp_hostname_sending_main.py "$@"

# Enable, disable, or check status of always-upgrade-on-boot
[positional-arguments]
@set-always-upgrade-on-boot *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/set_always_upgrade_on_boot.py "$@"

# Configure ptrace support (for anticheat, debugging tools, etc.)
[positional-arguments]
@set-ptrace *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/set_ptrace.py "$@"

alias set-anticheat-support := set-ptrace

# Boot into this device's BIOS/UEFI screen.
@bios:
    exec /usr/bin/python3 /usr/libexec/secureblue/bios.py

# Show all messages from this boot
@logs-this-boot:
    exec /usr/bin/run0 --via-shell journalctl -b 0

# Show all messages from last boot
@logs-last-boot:
    exec /usr/bin/run0 --via-shell journalctl -b -1
