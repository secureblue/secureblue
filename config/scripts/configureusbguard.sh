#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i 's/AuditBackend=FileAudit/AuditBackend=LinuxAudit/' /etc/usbguard/usbguard-daemon.conf
chmod 600 /etc/usbguard/rules.conf
