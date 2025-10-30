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

"""Remove Nvidia-specific kernel arguments."""

import subprocess  # nosec

import tomllib

with open("/usr/lib/bootc/kargs.d/20-nvidia.toml", "rb") as f:
    NVIDIA_KARGS = tomllib.load(f)["kargs"]

rpm_ostree_cmd = ["/usr/bin/rpm-ostree", "kargs"]
for karg in NVIDIA_KARGS:
    rpm_ostree_cmd.append(f"--delete-if-present={karg}")

print("Removing Nvidia-specific kernel arguments...")
subprocess.run(rpm_ostree_cmd, check=True)  # nosec
