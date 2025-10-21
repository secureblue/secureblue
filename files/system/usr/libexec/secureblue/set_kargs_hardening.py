#!/usr/bin/python3

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Add additional kernel arguments for hardening."""

# https://docs.kernel.org/admin-guide/kernel-parameters.html

import subprocess  # nosec
import sys
import textwrap

from kargs_hardening_common import (
    DEFAULT_KARGS,
    DISABLE_32_BIT,
    FORCE_NOSMT,
    MODULE_NO_SIG_ENFORCE,
    MODULE_SIG_ENFORCE,
    UNSTABLE_KARGS,
)

kargs_to_add = DEFAULT_KARGS
kargs_to_remove = []


def prompt_yes_no(message: str, *, default: bool = False) -> bool:
    """Prompt the user for a yes/no response."""
    yes_no = " [Y/n]: " if default else " [y/N]: "
    prompt = "\n" + textwrap.fill(textwrap.dedent(message.strip())) + yes_no
    while True:
        try:
            reply = input(prompt).casefold()
        except KeyboardInterrupt:
            print("\n\n[Interrupt received, exiting now.]", file=sys.stderr)
            sys.exit(130)
        if not reply:
            return default
        if reply.startswith("y"):
            return True
        if reply.startswith("n"):
            return False
        print("Invalid reponse, please enter 'y' or 'n'.")


msg = """
Do you need support for 32-bit processes/syscalls? (This is mostly used by
legacy software, with some exceptions, such as Steam.)
"""

if prompt_yes_no(msg):
    print("Keeping 32-bit support.")
    kargs_to_remove.append(DISABLE_32_BIT)
else:
    print("Disabling 32-bit support for the next boot.")
    kargs_to_add.append(DISABLE_32_BIT)

msg = """
Do you want to force disable Simultaneous Multithreading (SMT) / Hyperthreading?
(This can cause a reduction in the performance of certain tasks in favor of
security. Note that in most hardware SMT will be disabled anyways to mitigate
a known vulnerability; this turns it off on all hardware regardless.)
"""

if prompt_yes_no(msg):
    print("Force disabling SMT/hyperthreading.")
    kargs_to_add.append(FORCE_NOSMT)
else:
    print("Not force disabling SMT/hyperthreading.")
    kargs_to_remove.append(FORCE_NOSMT)

msg = """
Would you like to set additional (unstable) hardening kernel arguments?
(Warning: Setting these kernel arguments may lead to boot or stability issues
on some hardware.)
"""

if prompt_yes_no(msg):
    print("Setting unstable hardening kernel arguments.")
    kargs_to_add += UNSTABLE_KARGS
else:
    print("Not setting unstable hardening kernel arguments.")
    kargs_to_remove += UNSTABLE_KARGS

# Check for secure boot support, required for some drivers. (e.g. WiFi on some
# macbooks, plus there would be no way to verify these anyways.)
sb_state = subprocess.run(["/usr/bin/mokutil", "--sb-state"], capture_output=True, check=False)  # nosec
if (
    b"doesn't support Secure Boot" in sb_state.stderr
    or b"EFI variables are not supported" in sb_state.stderr
):
    print("Secure Boot not supported. Skipping module signature enforcement.")
    kargs_to_add.remove(MODULE_SIG_ENFORCE)
    kargs_to_add.append(MODULE_NO_SIG_ENFORCE)
    kargs_to_remove.append(MODULE_SIG_ENFORCE)
else:
    kargs_to_remove.append(MODULE_NO_SIG_ENFORCE)

rpm_ostree_cmd = ["/usr/bin/rpm-ostree", "kargs"]
for karg in kargs_to_add:
    rpm_ostree_cmd.append(f"--append-if-missing={karg}")
for karg in kargs_to_remove:
    rpm_ostree_cmd.append(f"--delete-if-present={karg}")

print("Applying boot parameters...")
subprocess.run(rpm_ostree_cmd, check=True)  # nosec
print("Hardening kernel arguments applied.")
