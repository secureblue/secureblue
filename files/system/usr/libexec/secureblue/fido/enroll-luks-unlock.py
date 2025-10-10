# Copyright (C) 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import sys

from utils import ConnectedDevices

connected_devices = ConnectedDevices()

if connected_devices.connected_device_count == 0:
    print("No compatible device detected!")
    sys.exit(0)
elif connected_devices.connected_device_count == 1:
    print("1 compatible device detected!\n")
else:
    print(f"{connected_devices.connected_device_count} compatible devices detected!\n")

connected_devices.prompt_select()

if len(connected_devices.selected) == 0:
    print("No device selected!")
    sys.exit(0)

# The set consist of indices (**as in ConnectedDevice.devices**) to be removed from ConnectedDevices.selected.
# If ConnectedDevices.selected = [1, 3, 4],
# remove_selected may be {3}, meaning that the element 3 in the array will be removed.
remove_selected = {}

for i in connected_devices.selected:
    device = connected_devices.devices[i]

    print(f"Scanning device {device.name}...\n")
    
    if device.cbor:
        device.test_supported_algorithms()
        device.test_bio_support()
    else:
        print("Automatic detection failed as device does not support CBOR.")
        print("This device will not be used.\n")
        remove_selected.add(i)

    device.device.close()

for i in remove_selected:
    # Use of remove() is okay as all elements in ConnectedDevices.selected should be unique.
    connected_devices.selected.remove(i)

print(
"""All devices scanned.
We will now proceed to...""")
