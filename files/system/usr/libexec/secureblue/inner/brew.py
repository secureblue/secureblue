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

"""
The sandboxed brew disable function
"""

import os
import shutil
import subprocess
import sys
from typing import Final

LINUXBREW_DIR: Final[str] = "/home/linuxbrew/.linuxbrew/"
BREW_ETC_STAMP: Final[str] = "/etc/.linuxbrew"


def main() -> int:
    """Enable or disable brew"""

    required_args_count = 2
    if len(sys.argv) != required_args_count:
        return 1

    mode = sys.argv[1]
    match mode:
        case "enable":
            systemctl = subprocess.run(  # nosec
                ["/usr/bin/systemctl", "enable", "--now", "brew-setup.service"],
                check=False,
                capture_output=True,
            )
            print("Brew is now enabled. Start a new shell to use brew.")
        case "disable":
            shutil.rmtree(LINUXBREW_DIR, ignore_errors=False)
            os.remove(BREW_ETC_STAMP)
            systemctl = subprocess.run(  # nosec
                ["/usr/bin/systemctl", "disable", "brew-setup.service"],
                check=False,
                capture_output=True,
            )

if __name__ == "__main__":
    sys.exit(main())
