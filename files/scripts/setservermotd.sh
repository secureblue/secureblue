#!/usr/bin/env bash

set -oue pipefail

sed -i 's/ujust --choose/ujust/' /usr/share/ublue-os/motd/secureblue.md
