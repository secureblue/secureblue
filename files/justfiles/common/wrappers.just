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

set positional-arguments := true

# Audit secureblue
audit-secureblue *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/audit_secureblue.py "$@"

# Run a non-flatpak application with standard memory allocator
[no-cd]
with-standard-malloc *args:
    #!/bin/sh
    LD_PRELOAD='' exec "$@"

# Sets bluetooth kernel modules on/off (requires reboot)
set-bluetooth-modules *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/bluetooth_main.py "$@"

# Interactively select secure DNS servers
dns-selector *args:
    #!/bin/sh
    exec /usr/bin/python3 /usr/libexec/secureblue/dns_selector.py "$@"
