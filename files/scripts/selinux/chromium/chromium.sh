#!/usr/bin/env bash

echo "Building and Loading Policy"

set -x

make -f /usr/share/selinux/devel/Makefile chromium.pp || exit
/usr/sbin/semodule -i chromium.pp

/sbin/restorecon -F -R -v /usr/lib/chromium-browser/
/sbin/restorecon -F -R -v /usr/lib/trivalent/
