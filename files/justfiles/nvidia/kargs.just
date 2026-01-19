# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Set Nvidia kernel arguments
set-kargs-nvidia:
    #!/usr/bin/sh
    /usr/bin/python3 /usr/libexec/secureblue/set_kargs_nvidia.py

# Remove Nvidia kernel arguments
remove-kargs-nvidia:
    #!/usr/bin/sh
    /usr/bin/python3 /usr/libexec/secureblue/remove_kargs_nvidia.py
