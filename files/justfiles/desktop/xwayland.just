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
    set -euo pipefail
    source /usr/lib/ujust/ujust.sh
    OPTION="{{ ACTION }}"
    if [ "$OPTION" = 'prompt' ]; then
      case "$(ujust get-image-name || echo 'unknown')" in
        silverblue-*)
          OPTION=gnome ;;
        kinoite-*)
          OPTION=plasma ;;
        sericea-*)
          OPTION=sway ;;
        *)
          echo "${bold}Toggling Xwayland (requires logout)${unbold}"
          echo 'For which DE/WM do you want to toggle Xwayland?'
          OPTION=$(ugum choose "GNOME" "KDE Plasma" "Sway")
          OPTION="${OPTION#KDE }"
          OPTION="${OPTION,,}"
          ;;
      esac
    fi
    case "$OPTION" in
    prompt) ;;
    gnome)
      GNOME_XWAYLAND_FILE='/etc/systemd/user/org.gnome.Shell@wayland.service.d/override.conf'
      if [ -e "$GNOME_XWAYLAND_FILE" ]; then
        rm -f "$GNOME_XWAYLAND_FILE"
        echo 'Xwayland for GNOME has been enabled.'
      else
        cp "/usr$GNOME_XWAYLAND_FILE" "$GNOME_XWAYLAND_FILE"
        chmod 644 "$GNOME_XWAYLAND_FILE"
        echo 'Xwayland for GNOME has been disabled.'
      fi
      ;;
    plasma)
      PLASMA_XWAYLAND_FILE='/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf'
      if [ -e "$PLASMA_XWAYLAND_FILE" ]; then
        rm -f "$PLASMA_XWAYLAND_FILE"
        echo 'Xwayland for KDE Plasma has been enabled.'
      else
        cp "/usr$PLASMA_XWAYLAND_FILE" "$PLASMA_XWAYLAND_FILE"
        chmod 644 "$PLASMA_XWAYLAND_FILE"
        echo 'Xwayland for KDE Plasma has been disabled.'
      fi
      ;;
    sway)
      SWAY_XWAYLAND_FILE='/etc/sway/config.d/99-noxwayland.conf'
      if [ -e "$SWAY_XWAYLAND_FILE" ]; then
        rm -f "$SWAY_XWAYLAND_FILE"
        echo 'Xwayland for Sway has been enabled.'
      else
        cp "/usr$SWAY_XWAYLAND_FILE" "$SWAY_XWAYLAND_FILE"
        chmod 644 "$SWAY_XWAYLAND_FILE"
        echo "Xwayland for Sway has been disabled."
      fi
      ;;
    help)
      echo "Usage: ujust toggle-xwayland [option]"
      echo "  [option]: Specify the quick option - 'gnome', 'plasma', or 'sway'"
      echo "  Use 'gnome' to toggle Xwayland for GNOME."
      echo "  Use 'plasma' to toggle Xwayland for KDE Plasma."
      echo "  Use 'sway' to toggle Xwayland for Sway."
      exit 0
      ;;
    *)
      echo "Unknown option '${OPTION}'." >&2
      exit 1
      ;;
    esac
