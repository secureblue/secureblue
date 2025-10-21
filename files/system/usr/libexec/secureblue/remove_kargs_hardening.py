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

"""Remove hardened kernel arguments."""

# https://docs.kernel.org/admin-guide/kernel-parameters.html

import subprocess  # nosec

from kargs_hardening_common import DEFAULT_KARGS, DISABLE_32_BIT, FORCE_NOSMT, UNSTABLE_KARGS

kargs_to_remove = DEFAULT_KARGS + DISABLE_32_BIT + FORCE_NOSMT + UNSTABLE_KARGS

rpm_ostree_cmd = ["/usr/bin/rpm-ostree", "kargs"]
for karg in kargs_to_remove:
    rpm_ostree_cmd.append(f"--delete-if-present={karg}")

print("Applying boot parameters...")
subprocess.run(rpm_ostree_cmd, check=True)  # nosec
print("Hardening kernel arguments removed.")
