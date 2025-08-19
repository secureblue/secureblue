# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
