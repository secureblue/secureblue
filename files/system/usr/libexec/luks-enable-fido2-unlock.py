# Copyright 2025 Universal Blue
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

from dataclasses import dataclass
from fido2.ctap2 import Ctap2
from fido2.hid import CAPABILITY, CtapHidDevice

import inquirer
import sys

# typedef for COSE algorithms reside in libfido2/src/fido/param.h
class COSEAlgorithms:
	ES256 = -7
	EDDSA = -8
	RS256 = -257

@dataclass
class ConnectedDevices:
	device: FIDODevice
	def __init__(self):
	

@dataclass
class FIDODevice:
    device: CtapHidDevice
    name: str
    selected: bool = False

    def get_name(self) -> list:
        # structure: [(name, index), (...)]
        names = []
        i = 0
        for device in self:
            names.append((device.name, i))
            i += 1
        return names

    def set_selected(self):
        self.selected = True

    def get_selected(self):
        return self.selected

    def get_capabilities(self):
        return self.device.capabilities

def enumerate_devices():
    connected_devices = []
    for device in CtapHidDevice.list_devices():
        connected_devices.append(FIDODevice(device))
    return connected_devices

connected_devices = enumerate_devices()

count_of_connected_devices = len(connected_devices)
if count_of_connected_devices == 0:
    print("No compatible devices detected!")
    sys.exit(0)
elif count_of_connected_devices == 1:
    print("1 compatible device detected!\n")
else:
    print("%d compatible devices detected!\n" % count_of_connected_devices)

checkbox = [
    inquirer.Checkbox(
        "devices",
        message="Which device(s) would you like to use?",
        choices=FIDODevice.get_name(connected_devices),
    ),
]

selected_devices = inquirer.prompt(checkbox)

indice_of_selected_devices = selected_devices.get("devices")

if len(indice_of_selected_devices) != 0:
    for i in indice_of_selected_devices:
        FIDODevice.set_selected(connected_devices[i])
else:
    print("No device selected!")
    sys.exit(0)

for device in connected_devices:
    if device.get_selected():
        if device.get_capabilities() & CAPABILITY.CBOR:
            ctap2 = Ctap2(device.device)
            info = ctap2.get_info()
            for supported_algorithms in info.algorithms:
            		match supported_algorithms.get('alg'):
            			case COSEAlgorithms.EDDSA:
            				print("Device reported support for EdDSA algorithm.")
            			case COSEAlgorithms.ES256:
            				print("Device reported support for ES256 algorithm.")
            			case COSEAlgorithms.RS256:
            				print("Device reported support for RS256 algorithm.")
        else:
            print("""Failed to detect supported algorithm as device does not support CBOR.
		    If you are sure that your device support a certain algorithm,
		    please rerun the script with --force --algorithm=(es256|rs256|eddsa)""") #FIXME
            sys.exit(0)

        device.device.close()
