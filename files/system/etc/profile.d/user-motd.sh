#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
#
# SPDX-License-Identifier: Apache-2.0

# Prevent doublesourcing
if [ -z "$USERMOTDSOURCED" ]; then
  USERMOTDSOURCED="Y"
  if test -d "$HOME"; then
    if test ! -e "$HOME"/.config/no-show-user-motd; then
      if test -x "/usr/libexec/ublue-motd"; then
        /usr/libexec/ublue-motd
      fi
    fi
  fi
fi
