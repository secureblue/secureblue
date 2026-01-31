#!/usr/bin/env bats

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

setup() {
    echo '
#!/bin/bash

# Define the version string
version="2024.9"

# Check if the --version argument is passed
if [[ "$1" == "--version" ]]; then
  echo "rpm-ostree:"
  echo " Version: '\''$version'\''"
else
  # Default behavior for unknown arguments (if you want to handle them)
  echo "Invalid option. Usage: rpm-ostree --version"
fi
    ' > rpm-ostree
    chmod +x rpm-ostree
    sudo cp -f rpm-ostree /usr/bin/rpm-ostree

}

@test "Script exits with error if rpm-ostree is not installed" {
  sudo mv /etc/os-release /etc/os-release.bak
  echo 'VARIANT="CoreOS"' | sudo tee /etc/os-release
  sudo bash -c 'mv /usr/bin/rpm-ostree /usr/bin/rpm-ostree.backup'
  run bash "$INSTALL_SCRIPT"
  [ "$status" -eq 1 ]
  [[ "$output" == *"This script only runs on Fedora Atomic"* ]]
  sudo bash -c 'mv /usr/bin/rpm-ostree.backup /usr/bin/rpm-ostree'
  sudo mv /etc/os-release.bak /etc/os-release
}

@test "Script exits with error if rpm-ostree is very old" {
  sudo mv /etc/os-release /etc/os-release.bak
  echo 'VARIANT="CoreOS"' | sudo tee /etc/os-release
  sudo sed -i 's/2024\.9/2023\.5/' /usr/bin/rpm-ostree
  run bash "$INSTALL_SCRIPT"
  [ "$status" -eq 1 ]
  [[ "$output" == *"rpm-ostree is too old, please upgrade before running this script."* ]]
  sudo sed -i 's/2023\.5/2024\.9/' /usr/bin/rpm-ostree
  sudo mv /etc/os-release.bak /etc/os-release
}

@test "Script exits with error if rpm-ostree is slightly old" {
  sudo mv /etc/os-release /etc/os-release.bak
  echo 'VARIANT="CoreOS"' | sudo tee /etc/os-release
  sudo sed -i 's/2024\.9/2024\.8/' /usr/bin/rpm-ostree
  run bash "$INSTALL_SCRIPT"
  [ "$status" -eq 1 ]
  [[ "$output" == *"rpm-ostree is too old, please upgrade before running this script."* ]]
  sudo sed -i 's/2024\.8/2024\.9/' /usr/bin/rpm-ostree
  sudo mv /etc/os-release.bak /etc/os-release
}

@test "Script works if rpm-ostree is new" {
  sudo mv /etc/os-release /etc/os-release.bak
  echo 'VARIANT="CoreOS"' | sudo tee /etc/os-release
  sudo sed -i 's/2024\.9/2024\.11/' /usr/bin/rpm-ostree
  run bash "$INSTALL_SCRIPT"
  [ "$status" -eq 0 ]
  sudo sed -i 's/2024\.11/2024\.9/' /usr/bin/rpm-ostree
  sudo mv /etc/os-release.bak /etc/os-release
}

@test "Script works if rpm-ostree is very new" {
  sudo mv /etc/os-release /etc/os-release.bak
  echo 'VARIANT="CoreOS"' | sudo tee /etc/os-release
  sudo sed -i 's/2024\.9/2025\.3/' /usr/bin/rpm-ostree
  run bash "$INSTALL_SCRIPT"
  [ "$status" -eq 0 ]
  sudo sed -i 's/2025\.3/2024\.9/' /usr/bin/rpm-ostree
  sudo mv /etc/os-release.bak /etc/os-release
}

@test "Script passes rpm-ostree check if it is installed" {
  sudo mv /etc/os-release /etc/os-release.bak
  echo 'VARIANT="CoreOS"' | sudo tee /etc/os-release
  run bash "$INSTALL_SCRIPT"
  [ "$status" -eq 0 ]
  [[ "$output" == *"Welcome to the secureblue interactive installer"* ]]
  sudo mv /etc/os-release.bak /etc/os-release
}

@test "Test command for securecore-zfs-main-hardened" {
  sudo mv /etc/os-release /etc/os-release.bak
  echo 'VARIANT="CoreOS"' | sudo tee /etc/os-release
  run bash -c "echo -e 'yes\nno\nno' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"securecore-zfs-main-hardened"* ]]
  sudo mv /etc/os-release.bak /etc/os-release
}

@test "Test command for securecore-main-hardened" {
  sudo mv /etc/os-release /etc/os-release.bak
  echo 'VARIANT="CoreOS"' | sudo tee /etc/os-release
  run bash -c "echo -e 'no\nno\nno' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"securecore-main-hardened"* ]]
  sudo mv /etc/os-release.bak /etc/os-release
}

