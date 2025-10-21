# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

# Set nvidia kargs
set-kargs-nvidia:
    #!/usr/bin/bash
    rpm-ostree kargs \
      --append-if-missing=rd.driver.blacklist=nouveau \
      --append-if-missing=modprobe.blacklist=nouveau \
      --append-if-missing=nvidia-drm.modeset=1 \
      --append-if-missing=nvidia-drm.fbdev=1

# Remove nvidia kargs
remove-kargs-nvidia:
    #!/usr/bin/bash
    rpm-ostree kargs \
      --delete-if-present=rd.driver.blacklist=nouveau \
      --delete-if-present=modprobe.blacklist=nouveau \
      --delete-if-present=nvidia-drm.modeset=1 \
      --delete-if-present=nvidia-drm.fbdev=1
