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

from dataclasses import dataclass, field

import inquirer
from fido2.ctap2 import Ctap2
from fido2.hid import CAPABILITY, CtapHidDevice


# typedef for COSE algorithms reside in libfido2/src/fido/param.h
class CoseAlgorithms:
    UNSPEC = 0
    ES256 = -7
    EDDSA = -8
    ECDH_ES256 = -25
    ES384 = -35
    RS256 = -257
    RS1 = -65535

@dataclass
class FidoDevice:
    device: CtapHidDevice
    # Same as self.device.product_name()
    name: str
    cbor: bool
    supported_algorithm: set[str] = field(default_factory=set)
    # True if the device is equipped with biometric sensor.
    bio: bool = False

    # Returns the path (/dev/hidrawX) of the device.
    def get_path(self) -> str:
        return self.device.descriptor.path

    # Test self.cbor before use!
    def test_supported_algorithms(self) -> None:
        supported_algorithms = Ctap2(self.device).get_info().algorithms

        for algo in supported_algorithms:
            match algo.get("alg"):
                case CoseAlgorithms.UNSPEC:
                    self.supported_algorithm.add("UNSPEC")
                case CoseAlgorithms.ES256:
                    self.supported_algorithm.add("ES256")
                case CoseAlgorithms.EDDSA:
                    self.supported_algorithm.add("EDDSA")
                case CoseAlgorithms.ECDH_ES256:
                    self.supported_algorithm.add("ECDH_ES256")
                case CoseAlgorithms.ES384:
                    self.supported_algorithm.add("ES384")
                case CoseAlgorithms.RS256:
                    self.supported_algorithm.add("RS256")
                case CoseAlgorithms.RS1:
                    self.supported_algorithm.add("RS1")

    # Test self.cbor before use!
    def test_bio_support(self) -> None:
        info = Ctap2(self.device).get_info()

        if (( "bioEnroll" in info.options ) or
            ("FIDO_2_1_PRE" in info.versions
            and "userVerificationMgmtPreview" in info.options )
        ):
            self.bio = True

@dataclass
class ConnectedDevices:
    devices: list[FidoDevice] = field(default_factory=list)
    # Total number of devices connected
    connected_device_count: int = 0
    # A list storing indices of the devices (**as in ConnectedDevices.devices**) selected
    selected: list[int] = field(default_factory=list)

    # Enumerate devices, stores a list of FidoDevice in ConnectedDevices.devices.
    def __init__(self):
        self.devices = []
        self.selected = []
        self.refresh_connected_devices()

    def refresh_connected_devices(self) -> None:
        self.devices = []
        self.connected_device_count = 0
        self.selected = []

        for device in CtapHidDevice.list_devices():
            cbor_support = device.capabilities & CAPABILITY.CBOR
            self.devices.append(FidoDevice(device, device.product_name, cbor_support))
            self.connected_device_count += 1

    # Enumerate through list ConnectedDevices.devices.
    # Append the name of each device and it's index to list_enumerated.
    # (Intended for use with prompt_select()).
    def enumerate_list(self) -> list[(str, int)]:
        list_enumerated = []
        for i, device in enumerate(self.devices):
            list_enumerated.append((device.name, i))
        return list_enumerated

    def prompt_select(self) -> None:
        checkbox = [
            inquirer.Checkbox(
                "devices",
                message="Which device(s) would you like to use?",
                choices=self.enumerate_list(),
            ),
        ]

        # inquirer.prompt(checkbox).get("devices") is a list of indices (**as in ConnectedDevices.devices**) of the selected devices
        self.selected = inquirer.prompt(checkbox).get("devices")
