#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

systemctl disable uresourced.service
systemctl mask uresourced.service

systemctl disable low-memory-monitor.service
systemctl mask low-memory-monitor.service

systemctl disable thermald.service
systemctl mask thermald.service
