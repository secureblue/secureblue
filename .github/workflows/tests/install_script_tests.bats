#!/usr/bin/env bats

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
  sudo bash -c 'mv /usr/bin/rpm-ostree /usr/bin/rpm-ostree.backup'
  run bash "$INSTALL_SCRIPT"
  [ "$status" -eq 1 ]
  [[ "$output" == *"This script only runs on Fedora Atomic"* ]]
  sudo bash -c 'mv /usr/bin/rpm-ostree.backup /usr/bin/rpm-ostree'
}

@test "Script exits with error if rpm-ostree is very old" {
  sudo sed -i 's/2024\.9/2023\.5/' /usr/bin/rpm-ostree
  run bash "$INSTALL_SCRIPT"
  [ "$status" -eq 1 ]
  [[ "$output" == *"rpm-ostree is too old, please upgrade before running this script."* ]]
  sudo sed -i 's/2023\.5/2024\.9/' /usr/bin/rpm-ostree
}

@test "Script exits with error if rpm-ostree is slightly old" {
  sudo sed -i 's/2024\.9/2024\.8/' /usr/bin/rpm-ostree
  run bash "$INSTALL_SCRIPT"
  [ "$status" -eq 1 ]
  [[ "$output" == *"rpm-ostree is too old, please upgrade before running this script."* ]]
  sudo sed -i 's/2024\.8/2024\.9/' /usr/bin/rpm-ostree
}

@test "Script works if rpm-ostree is new" {
  sudo sed -i 's/2024\.9/2024\.11/' /usr/bin/rpm-ostree
  run bash "$INSTALL_SCRIPT"
  [ "$status" -eq 0 ]
  sudo sed -i 's/2024\.11/2024\.9/' /usr/bin/rpm-ostree
}

@test "Script works if rpm-ostree is very new" {
  sudo sed -i 's/2024\.9/2025\.3/' /usr/bin/rpm-ostree
  run bash "$INSTALL_SCRIPT"
  [ "$status" -eq 0 ]
  sudo sed -i 's/2025\.3/2024\.9/' /usr/bin/rpm-ostree
}

@test "Script passes rpm-ostree check if it is installed" {
  run bash "$INSTALL_SCRIPT"
  [ "$status" -eq 0 ]
  [[ "$output" == *"Welcome to the secureblue interactive installer"* ]]
}

@test "Test command for silverblue-main-hardened" {
  run bash -c "echo -e 'no\n1\nno\nno' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"silverblue-main-hardened"* ]]
}

@test "Test command for silverblue-nvidia-hardened" {
  run bash -c "echo -e 'no\n1\nyes\nno\nno' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"silverblue-nvidia-hardened"* ]]
}


@test "Test command for silverblue-nvidia-open-hardened" {
  run bash -c "echo -e 'no\n1\nyes\nyes\no\nno' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"silverblue-nvidia-open-hardened"* ]]
}

@test "Test command for kinoite-main-hardened" {
  run bash -c "echo -e 'no\n2\nno\nno' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"kinoite-main-hardened"* ]]
}

@test "Test command for sericea-main-hardened" {
  run bash -c "echo -e 'no\n3\nno\nno' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"sericea-main-hardened"* ]]
}

@test "Test command for wayblue-wayfire-main-hardened" {
  run bash -c "echo -e 'no\n4\nno\nno' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"wayblue-wayfire-main-hardened"* ]]
}

@test "Test command for wayblue-sway-main-hardened" {
  run bash -c "echo -e 'no\n5\nno\nno' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"wayblue-sway-main-hardened"* ]]
}

@test "Test command for wayblue-river-main-hardened" {
  run bash -c "echo -e 'no\n6\nno\nno' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"wayblue-river-main-hardened"* ]]
}

@test "Test command for wayblue-hyprland-main-hardened" {
  run bash -c "echo -e 'no\n7\nno\nno' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"wayblue-hyprland-main-hardened"* ]]
}

@test "Test command for cosmic-main-hardened" {
  run bash -c "echo -e 'no\n8\nno\nno' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"cosmic-main-hardened"* ]]
}

@test "Test command for securecore-zfs-main-hardened" {
  sudo mv /etc/os-release /etc/os-release.bak
  echo 'VARIANT="CoreOS"' | sudo tee /etc/os-release
  run bash -c "echo -e 'yes\nyes\nno\no' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"securecore-zfs-main-hardened"* ]]
  sudo mv /etc/os-release.bak /etc/os-release
}

@test "Test command for securecore-main-hardened" {
  sudo mv /etc/os-release /etc/os-release.bak
  echo 'VARIANT="CoreOS"' | sudo tee /etc/os-release
  run bash -c "echo -e 'yes\nno\nno\no' | bash '$INSTALL_SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == *"securecore-main-hardened"* ]]
  sudo mv /etc/os-release.bak /etc/os-release
}

