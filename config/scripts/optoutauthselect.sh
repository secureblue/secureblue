#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "Opting-out of 'authselect' profile generation"

rm /etc/authselect/authselect.conf
authselect opt-out 1> /dev/null