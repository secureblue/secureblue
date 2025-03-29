#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

systemctl --global enable secureblue-key-enrollment-verification.timer
