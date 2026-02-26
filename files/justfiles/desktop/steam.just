# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Install Steam via choice of 2 methods
install-steam:
    #!/usr/bin/bash
    if [ -z "$(pgrep Xwayland)" ] && [ -z "$(pgrep Xorg)" ] ; then
        echo "Steam requires X or Xwayland, which your variant of secureblue has disabled by default."
        echo "Please run 'ujust set-xwayland on' to re-enable it."
        enable_xwayland_now=""
        read -rp "Would you like to run 'ujust set-xwayland on' now? [Y/n] " enable_xwayland_now
        enable_xwayland_now=${enable_xwayland_now:-y}
        if [[ "$enable_xwayland_now" == [Yy]* ]]; then
            echo "Running 'ujust set-xwayland on'"
            ujust set-xwayland on
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
    echo "Please select a method to install Steam:"
    echo "    1) Flatpak - Install the Steam flatpak from flathub-unverified (Recommended for most users)"
    echo "    2) Distrobox - Install Steam via the bazzite-arch distrobox image (Recommended for SteamVR users)"
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
