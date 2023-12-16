#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "

# Disables user namespaces
# DO NOT REMOVE
# https://github.com/containers/bubblewrap/security/advisories/GHSA-j2qp-rvxj-43vj
user.max_user_namespaces = 0
kernel.unprivileged_userns_clone = 0

" >> /usr/etc/sysctl.d/hardening.conf

