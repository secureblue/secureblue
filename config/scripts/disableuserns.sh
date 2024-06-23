#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "

# Disables user namespaces
# DO NOT REMOVE
# https://github.com/containers/bubblewrap/security/advisories/GHSA-j2qp-rvxj-43vj
user.max_user_namespaces = 0

" >> /usr/etc/sysctl.d/hardening.conf

mkdir -p /usr/etc/systemd/system/upower.service.d/

echo "

[Service]
# Namespaces
PrivateUsers=no
RestrictNamespaces=no

" >> /usr/etc/systemd/system/upower.service.d/namespaces.conf

chown root:root /usr/bin/bwrap
chmod u+s /usr/bin/bwrap

