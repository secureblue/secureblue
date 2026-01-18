#!/usr/bin/sh

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

case $- in
  *i*)
    if ! command -v sudo > /dev/null; then
      sudo() {
        printf 'Secureblue uninstalls \033[1msudo\033[22m for security reasons.\n' >&2
        printf 'To run commands as root, you can use \033[1mrun0\033[22m instead.\n' >&2
        printf 'To get a root shell, run \033[1mrun0\033[22m on its own.\n' >&2
        command sudo "$@"
      }
    fi
    ;;
esac
