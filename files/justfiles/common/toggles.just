# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# enable a kernel module that is disabled by modprobe.d (requires restart)
[positional-arguments]
@override-enable-module mod_name:
    exec /usr/libexec/secureblue/override-enable-module "$@"

# reset the override by `just override-enable-module`, i.e. disable the module again (requires restart)
[positional-arguments]
@override-reset-module mod_name:
    exec /usr/libexec/secureblue/override-reset-module "$@"

# Toggle bash environment lockdown (mitigates LD_PRELOAD attacks). Use skip_approval to bypass initial prompt, and apply_for_all_users to bypass secondary prompt.
[positional-arguments]
@toggle-bash-environment-lockdown skip_approval="false" apply_for_all_users="prompt":
    exec /usr/libexec/secureblue/toggle-bash-environment-lockdown "$@"
   
# Toggle MAC Randomization
@toggle-mac-randomization:
    exec /usr/libexec/secureblue/toggle-mac-randomization