#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sudo sed -i 's/AuditBackend=FileAudit/AuditBackend=LinuxAudit/' /etc/usbguard/usbguard-daemon.conf
sudo chmod 600 /etc/usbguard/rules.conf
