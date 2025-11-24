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

# Toggle Xwayland support
toggle-xwayland ACTION="prompt":
    #! /bin/run0 /bin/bash
    source /usr/lib/ujust/ujust.sh
    OPTION="{{ ACTION }}"
    if [ "$OPTION" = "prompt" ]; then
      IMAGE="$(rpm-ostree status | grep '●')"
      if echo "$IMAGE" | grep -q 'silverblue'; then
          OPTION=gnome
      elif echo "$IMAGE" | grep -q 'kinoite'; then
          OPTION=plasma
      elif echo "$IMAGE" | grep -qE 'sericea|sway'; then
          OPTION=sway
      else
        echo "${bold}Toggling Xwayland (requires logout)${unbold}"
        echo 'For which DE/WM do you want to toggle Xwayland?'
        OPTION=$(ugum choose "GNOME" "KDE Plasma" "Sway")
      fi
    elif [ "$OPTION" = "help" ]; then
      echo "Usage: ujust toggle-xwayland <option>"
      echo "  <option>: Specify the quick option - 'gnome', 'plasma', or 'sway'"
      echo "  Use 'gnome' to Toggle Xwayland for GNOME."
      echo "  Use 'plasma' to Toggle Xwayland for KDE Plasma."
      echo "  Use 'sway' to Toggle Xwayland for Sway."
      exit 0
    fi
    if [ "${OPTION,,}" = "gnome" ]; then
      GNOME_XWAYLAND_FILE='/etc/systemd/user/org.gnome.Shell@wayland.service.d/override.conf'
      if [ -e "$GNOME_XWAYLAND_FILE" ]; then
        rm -f "$GNOME_XWAYLAND_FILE"
        echo 'Xwayland for GNOME has been enabled.'
      else
        cp "/usr$GNOME_XWAYLAND_FILE" "$GNOME_XWAYLAND_FILE"
        chmod 644 "$GNOME_XWAYLAND_FILE"
        echo 'Xwayland for GNOME has been disabled.'
      fi
    elif [ "$OPTION" = "KDE Plasma" ] || [ "${OPTION,,}" = "plasma" ]; then
      PLASMA_XWAYLAND_FILE='/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf'
      if [ -e "$PLASMA_XWAYLAND_FILE" ]; then
        rm -f "$PLASMA_XWAYLAND_FILE"
        echo 'Xwayland for KDE Plasma has been enabled.'
      else
        cp "/usr$PLASMA_XWAYLAND_FILE" "$PLASMA_XWAYLAND_FILE"
        chmod 644 "$PLASMA_XWAYLAND_FILE"
        echo 'Xwayland for KDE Plasma has been disabled.'
      fi
    elif [ "${OPTION,,}" = "sway" ]; then
      SWAY_XWAYLAND_FILE='/etc/sway/config.d/99-noxwayland.conf'
      if [ -e "$SWAY_XWAYLAND_FILE" ]; then
        rm -f "$SWAY_XWAYLAND_FILE"
        echo 'Xwayland for Sway has been enabled.'
      else
        cp "/usr$SWAY_XWAYLAND_FILE" "$SWAY_XWAYLAND_FILE"
        chmod 644 "$SWAY_XWAYLAND_FILE"
        echo "Xwayland for Sway has been disabled."
      fi
    fi
