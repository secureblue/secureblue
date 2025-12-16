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

# Install Steam via choice of 2 methods
install-steam:
    #!/usr/bin/bash
    if [ -z "$(pgrep Xwayland)" ] && [ -z "$(pgrep Xorg)" ] ; then
        echo "Steam requires X or Xwayland, which your variant of secureblue has disabled by default."
        echo "Please run 'ujust toggle-xwayland' to re-enable it."
        toggle_xwayland_now=""
        read -rp "Would you like to run 'ujust toggle-xwayland' now? [Y/n] " toggle_xwayland_now
        toggle_xwayland_now=${toggle_xwayland_now:-y}
        if [[ "$toggle_xwayland_now" == [Yy]* ]]; then
            echo "Running 'ujust toggle-xwayland'"
            ujust toggle-xwayland
            reboot_now=""
            read -rp "Would you like to reboot now? [y/N] " reboot_now
            if [[ "$reboot_now" == [Yy]* ]]; then
                echo "Rebooting"
                systemctl reboot
            fi
        fi
    fi
    valid_input="0"
    method_selection=""
    echo "Please select a method to install steam:"
    echo "    1) Flatpak - will install the steam flatpak from flathub-unverified"
    echo "    2) Distrobox - will set up steam via the bazzite-arch distrobox image"
    while [[ "$valid_input" == "0" ]]; do
        read -rp "Selection [1-2]: " method_selection
        if [[ "$method_selection" == [12]* ]]; then
            valid_input="1"
        else
            echo "That is not a valid selection."
        fi
    done

    echo "" # blank space
    case "$method_selection" in
        1)
            echo "Flatpak method selected."
            echo "Enabling the unfiltered Flathub repo."
            ujust enable-flathub-unfiltered
            echo "Installing Steam flatpak."
            flatpak install -y flathub com.valvesoftware.Steam
            echo "Disabling hardened_malloc for Steam."
            flatpak override --user --unset-env=LD_PRELOAD --nofilesystem=host-os com.valvesoftware.Steam

            echo "" # spaced out to be more obvious and for ease of reading
            echo "Granting Steam necessary permissions for basic functionality, including access to X11 and PulseAudio."
            echo "This will override the flatpak-permissions-lockdown command, or any other global overrides."
            echo "Note that to use controllers, you must additionally grant device=input if it is globally denied."
            echo "Games with anti-cheats will likely require granting allow=devel alongside running ujust toggle-anticheat-support."
            flatpak override --user --share=network --share=ipc --socket=x11 --socket=pulseaudio --allow=multiarch --allow=per-app-dev-shm com.valvesoftware.Steam
            echo ""
            ;;
        2)
            echo "Distrobox method selected."
            if [[ "$(ujust set-container-userns status)" == "disabled" ]]; then
                echo "Distrobox requires container domain user namespaces to work, which are disabled by default for security reasons."
                echo "You need to run 'ujust set-container-userns on' to allow this."
                container_userns_now=""
                read -rp "Would you like to run 'ujust set-container-userns on' now? [Y/n] " container_userns_now
                container_userns_now=${container_userns_now:-y}
                if [[ "$container_userns_now" == [Yy]* ]]; then
                    echo "Running 'ujust set-container-userns on'"
                    ujust set-container-userns on
                fi
            fi
            echo "Creating bazzite-arch distrobox."
            distrobox-create --unshare-netns --nvidia --image ghcr.io/ublue-os/bazzite-arch --name bazzite-arch -Y
            echo "Exporting Steam from bazzite-arch distrobox."
            distrobox-enter -n bazzite-arch -- distrobox-export --app steam
            ;;
    esac

    echo "Steam requires support for 32-bit processes/syscalls."
    if rpm-ostree kargs | grep -q 'ia32_emulation=0'; then
        echo "This script will now remove the 'ia32_emulation=0' kernel argument."
        rpm-ostree kargs --delete-if-present="ia32_emulation=0"
    else
        echo "Do not set the 'ia32_emulation=0' kernel argument."
    fi
