#!/usr/bin/env bash

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

set -oue pipefail

sed '/\[Service\]/i #\ Secureblue\ Hardening\nStopWhenUnneeded=true\nRefuseManualStart=true\n#\ End\ of\ Secureblue\ Hardening\n' "/usr/lib/systemd/system/avahi-daemon.service" | tee /usr/lib/systemd/system/avahi-daemon.service
sed '/\[Socket\]/i #\ Secureblue\ Hardening\nStopWhenUnneeded=true\nRefuseManualStart=true\n#\ End\ of\ Secureblue\ Hardening\n' "/usr/lib/systemd/system/avahi-daemon.socket" | tee /usr/lib/systemd/system/avahi-daemon.socket
