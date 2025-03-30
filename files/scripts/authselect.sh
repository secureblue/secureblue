#!/usr/bin/env bash

set -oue pipefail

echo "Enabling faillock in PAM authentication profile"

authselect enable-feature with-faillock 1> /dev/null