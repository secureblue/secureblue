#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# Check if ublue-os-update-services rpm is installed, these services conflict with ublue-update
if rpm -q ublue-os-update-services > /dev/null; then
    rpm-ostree override remove ublue-os-update-services
fi

# Change the conflicting update policy for rpm-ostreed
RPM_OSTREE_CONFIG="/usr/etc/rpm-ostreed.conf"

if [[ -f $RPM_OSTREE_CONFIG ]]; then
    if [[ "$(get_config_value AutomaticUpdatePolicy $RPM_OSTREE_CONFIG)" == "stage" ]]; then
        set_config_value AutomaticUpdatePolicy none $RPM_OSTREE_CONFIG
    fi
fi

rpm-ostree install "$BLING_DIRECTORY"/rpms/ublue-update*.rpm
