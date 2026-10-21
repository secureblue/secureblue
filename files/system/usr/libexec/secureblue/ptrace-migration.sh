#!/bin/sh

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -eu

ptrace_scope=$(grep -oP '^kernel.yama.ptrace_scope\s*=\s*\K[0-9]+' /etc/sysctl.d/61-ptrace-scope.conf 2>/dev/null || echo 3)

case "${ptrace_scope}" in
    0|1) ujust set-ptrace on ;;
    2) ujust set-ptrace container ;;
esac

rm -f /etc/sysctl.d/61-ptrace-scope.conf
