#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i 's/countdown = false/countdown = true/g' /usr/etc/security/authramp.conf

