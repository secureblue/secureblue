#!/usr/bin/env bash

echo "Building and Loading Policy"

set -x

make -f /usr/share/selinux/devel/Makefile trivalent.pp || exit
/usr/sbin/semodule -i trivalent.pp -v 

/sbin/restorecon -F -R -v /usr/lib/trivalent/
