# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

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
    #!/usr/bin/sh
    /usr/bin/python3 /usr/libexec/secureblue/set_kargs_hardening.py

# Remove all hardening boot parameters (requires reboot)
remove-kargs-hardening:
    #!/usr/bin/sh
    /usr/bin/python3 /usr/libexec/secureblue/remove_kargs_hardening.py

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
