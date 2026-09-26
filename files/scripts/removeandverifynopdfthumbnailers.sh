#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

dnf remove -y papers-thumbnailer

rm -f /usr/lib64/qt6/plugins/kf6/thumbcreator/gsthumbnail.so
rm -f /usr/lib64/tumbler-1/plugins/tumbler-poppler-thumbnailer.so

if grep -rq application/pdf /usr/share/thumbnailers /usr/lib64/qt6/plugins/kf6/thumbcreator /usr/lib64/tumbler-1/plugins 2> /dev/null
then
    echo "Failed to remove all pdf thumbnailers"
    exit 1
fi
