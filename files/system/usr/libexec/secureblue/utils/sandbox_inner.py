"""
sandbox_inner.py

This script executes the called function with elevated permissions.
"""

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

import sys
import os
import pickle  # nosec
import base64
import importlib.util


# From https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly which is under a Zero Clause BSD License
def import_from_path(module_name, file_path):
    """Imports the file into python global context."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def main():
    """Handles sandboxed function args, return, and calling."""
    b64_str = os.environ.get("python_config")
    if b64_str is None:
        print("Environment variable 'python_config' not set", file=sys.stderr)
        return 1
    pickle_input_dump = base64.b64decode(b64_str)
    func_list = pickle.loads(pickle_input_dump)
    module = import_from_path("python_file", func_list[1])
    args = func_list[2] if len(func_list) > 2 else []
    kwargs = func_list[3] if len(func_list) > 3 else {}
    func_call = getattr(module, func_list[0])
    func_return = func_call(*args, **kwargs)  # actually runs function
    return_obj = base64.b64encode(pickle.dumps(func_return)).decode("ascii")
    print(return_obj, end="", file=sys.stderr)  # puts return object to stderr as str
    return 0


if __name__ == "__main__":
    sys.exit(main())
