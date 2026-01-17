#!/usr/bin/env python3


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
Toggle display of the user-motd in terminal
"""
from pathlib import Path
import os

# Extra parentheses added so python doesn't check the individual string instead of the path
if (Path.home() / ".config" / "no-show-user-motd").is_file():
    os.remove(Path.home() / ".config" / "no-show-user-motd")
    print("MOTD enabled.")

else:
    if (Path.home() / ".config").is_dir() != True:
        os.mkdir(Path.home() / ".config(")
    open(Path.home() / ".config" / "no-show-user-motd", "x")
    print("MOTD disabled.")



# if __name__ == "__main__":
    # sys.exit(main())
