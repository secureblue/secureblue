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
A class that wraps a function to be run in a sandbox
"""


class SandboxedFunction:
    """A class that wraps a function to be run in a sandbox"""

    def __init__(
        self, caps: list[str] | None, rw_paths: list[str] | None, sbox_props: list[str] | None
    ):
        """Initialize the sandboxed function with required caps, rw_paths, and additional props"""
        self.caps = caps
        self.rw_paths = rw_paths
        self.sbox_props = sbox_props

    def inner_file_name(self) -> str:
        """Return the target file name"""
        return f"{self.__class__.__name__.lower()}.py"

    def capabilities(self) -> list[str] | None:
        """Return the function's required caps"""
        return self.caps

    def read_write_paths(self) -> list[str] | None:
        """Return the function's required rw paths"""
        return self.rw_paths

    def additional_sandbox_properties(self) -> list[str] | None:
        """Return the function's required additional sandbox properties"""
        return self.sbox_props
