#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Prevent doublesourcing
if [ -z "${USERMOTDSOURCED-}" ]; then
  USERMOTDSOURCED='Y'
  if [ -d "$HOME" ] && ! [ -e "$HOME/.config/no-show-user-motd" ] && [ -x '/usr/libexec/secureblue-motd' ]; then
    /usr/libexec/secureblue-motd
  fi
fi
