# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Toggle GHNS (KDE Get New Stuff)
toggle-ghns:
    #! /bin/run0 /bin/bash
    KDE_GLOBALS_FILE='/etc/xdg/kdeglobals'
    if test -e "$KDE_GLOBALS_FILE"; then
      if grep -q '^ghns=false' "$KDE_GLOBALS_FILE"; then
        sed -i 's/^ghns=false.*/ghns=true/' "$KDE_GLOBALS_FILE"
        echo 'GHNS enabled.'
      elif grep -q '^ghns=true' "$KDE_GLOBALS_FILE"; then
        sed -i 's/^ghns=true.*/ghns=false/' "$KDE_GLOBALS_FILE"
        echo 'GHNS disabled.'
      else
        echo 'The kdeglobals file is missing the ghns toggle.'
      fi
    else
      echo 'No kdeglobals file found. Are you on kinoite?'
    fi
