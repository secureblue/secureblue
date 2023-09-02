#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# Check if ublue-os-update-services rpm is installed, these services conflict with ublue-update
if rpm -q ublue-os-update-services > /dev/null; then
    rpm-ostree override remove ublue-os-update-services
fi
rpm-ostree install "$BLING_DIRECTORY"/rpms/ublue-update*.rpm