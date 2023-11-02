#!/usr/bin/env bash

# Tell this script to exit if there are any errors.
# You should have this in every custom script, to ensure that your completed
# builds actually ran successfully without any errors!
set -oue pipefail

echo "Installing chromium from rawhide"
koji download-build --arch=x86_64 $(koji latest-build rawhide chromium | awk 'NR==3 {print $1}')
rpm-ostree install *.rpm