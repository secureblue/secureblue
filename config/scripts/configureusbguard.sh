#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i 's/AuditBackend=FileAudit/AuditBackend=LinuxAudit/' /usr/etc/usbguard/usbguard-daemon.conf
chmod 600 /usr/etc/usbguard/rules.conf
