#!/usr/bin/env bash

set -oue pipefail

systemctl --global enable secureblue-key-enrollment-verification.timer
