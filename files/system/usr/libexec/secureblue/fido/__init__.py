#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

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
    # From self.device.product_name()
    name: str
    __cbor_support: bool
    # Set of integers with definitions defined in class CoseAlgorithms
    __supported_algorithms: set[int] = field(default_factory=set)
    # True if the device is equipped with biometric sensor, and the user wants to use it.
    __use_bio: bool = False

    def test_supported_algorithm(self) -> None:
        if not self.__cbor_support:
            raise RuntimeError("Device does not support CBOR")

        supported_algorithms = Ctap2(self.device).get_info().algorithms

        for element in supported_algorithms:
            self.__supported_algorithms.add(element.get("alg"))

    def test_bio_support(self) -> bool:
        if not self.__cbor_support:
            raise RuntimeError("Device does not support CBOR")

        info = Ctap2(self.device).get_info()

        return ("bioEnroll" in info.options) or (
            "FIDO_2_1_PRE" in info.versions
            and "userVerificationMgmtPreview" in info.options
        )

    def close(self) -> None:
        self.device.close()

    # Getters & Setters
    def get_cbor_support(self) -> bool:
        return self.__cbor_support

    def set_use_bio(self, value: bool) -> None:
        self.__bio = value

    def get_use_bio(self) -> bool:
        return self.__bio

    # Returns the path (/dev/hidrawX) of the device.
    def get_path(self) -> str:
        return self.device.descriptor.path

    def get_supported_algorithms(self) -> set:
        return self.__supported_algorithms


@dataclass
class ConnectedDevices:
    __devices: list[FidoDevice] = field(default_factory=list)
    # Total number of devices connected
    __count: int = 0

    # Enumerate devices, stores a list of FidoDevice in ConnectedDevices.devices.
    def __init__(self):
        self.devices = []
        self.refresh_connected_devices()

    def refresh_connected_devices(self) -> None:
        self.devices = []
        self.count = 0

        for device in CtapHidDevice.list_devices():
            cbor_support = bool(device.capabilities & CAPABILITY.CBOR)
            self.devices.append(FidoDevice(device, device.product_name, cbor_support))
            self.count += 1

    # Enumerate through list ConnectedDevices.devices.
    # Append the name of each device and it's index to list_enumerated.
    # (Intended for use with prompt_select() only).
    def enumerate_list(self) -> list[(str, int)]:
        list_enumerated = []
        for i, device in enumerate(self.get_devices()):
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

        # inquirer.prompt(checkbox).get("devices") is a list of indices
        # (**as in ConnectedDevices.devices**) of the selected devices
        selected_devices = inquirer.prompt(checkbox).get("devices")

        # Remove non-selected devices from list
        for i in range(self.count - 1, -1, -1):
            if i not in selected_devices:
                self.devices.pop(i)
                self.count -= 1

    # Getters & Setters
    def get_count(self) -> int:
        return self.count

    def get_devices(self) -> list[FidoDevice]:
        return self.devices
