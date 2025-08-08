#!/usr/bin/env bash

# SPDX-FileCopyrightText 2025 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0 OR MIT

echo "Building and Loading Policy"

set -x

make -f /usr/share/selinux/devel/Makefile nautilus.pp || exit
/usr/sbin/semodule -i nautilus.pp

/sbin/restorecon -F -R -v /usr/bin/nautilus
