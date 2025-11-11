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

from kargs_hardening_common import (
    DEFAULT_KARGS,
    DISABLE_32_BIT,
    FORCE_NOSMT,
    UNSTABLE_KARGS,
    apply_kargs,
)


def main() -> None:
    """Main script entry point."""
    kargs_to_remove = [*DEFAULT_KARGS, DISABLE_32_BIT, FORCE_NOSMT, *UNSTABLE_KARGS]

    print("Applying boot parameters...")
    apply_kargs(add=[], remove=kargs_to_remove)
    print("Hardening kernel arguments removed.")


if __name__ == "__main__":
    main()
