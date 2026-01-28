# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Install Steam via choice of 2 methods
install-steam:
    #!/usr/bin/bash
    echo "############# 32-BIT ARCHITETURE SUPPORT #############"
    echo
    echo "32-bit architecture support is required for Steam to function."
    if rpm-ostree kargs | grep -q 'ia32_emulation=0'; then
        echo
        echo "'ia32_emulation=0' has been detected in your kernel arguments (it's not enabled by default)."
        echo "The script will now remove it from your kernel arguments as to allow Steam to function properly."
        rpm-ostree kargs --delete-if-present="ia32_emulation=0"
        echo "Kernel argument removed."
    else
        echo "Do not add 'ia32_emulation=0' to your kernel arguments, as that would cause Steam to cease functioning."
    fi

    if [ -z "$(pgrep Xwayland)" ] && [ -z "$(pgrep Xorg)" ]; then
        echo
        echo "############# XWAYLAND SUPPORT #############"
        echo
        echo "Steam requires Xwayland (or a full X server, which is not recommended) to function. Your variant of secureblue has disabled it by default."
        echo "Please run 'ujust set-xwayland on' to re-enable it."
        echo
        read -rp "Would you like to run 'ujust set-xwayland on' now? [Y/n] " enable_xwayland_now
        enable_xwayland_now=${enable_xwayland_now:-y}
        if [[ "$enable_xwayland_now" == [Yy]* ]]; then
            echo
            echo "Running 'ujust set-xwayland on'"
            ujust set-xwayland on
        fi
    fi

    if [[ "$(sysctl -n kernel.yama.ptrace_scope)" != "1" ]]; then
        echo
        echo "############# ANTI-CHEAT SUPPORT #############"
        echo
        echo "Some on-line games require process tracing support to make their anti-cheats solutions work as expected. Examples of solutions are Easy Anti-Cheat and BattlEye."
        echo "By default, secureblue does not allow ptrace attachment at all, in order to address basic security concerns."
        echo
        echo "Would you like to enable anti-cheat support?"
        echo "This will run 'ujust toggle-anticheat-support'."
        echo
        read -rp "Would you like to run 'ujust toggle-anticheat-support' now? [Y/n] " enable_anticheat_now
        enable_anticheat_now=${enable_anticheat_now:-y}
        if [[ "$enable_anticheat_now" == [Yy]* ]]; then
            echo
            echo "Running 'ujust toggle-anticheat-support'"
            echo
            ujust toggle-anticheat-support
        fi
    fi

    valid_input="0"
    method_selection=""
    echo
    echo "############# STEAM INSTALLATION #############"
    echo
    echo "Select a method to install Steam:"
    echo "(1) Flatpak — will install the Steam Flatpak package from the unfiltered Flathub repository (recommended option)"
    echo "(2) Distrobox — will set up Steam via the bazzite-arch distrobox image"
    while [[ "$valid_input" == "0" ]]; do
        read -rp "Selection (1 or 2): " method_selection
        if [[ "$method_selection" == "1" || "$method_selection" == "2" ]]; then
            valid_input="1"
        else
            echo "Invalid selection."
        fi
    done

    case "$method_selection" in
        1)
            echo "Flatpak method selected."
            echo "Enabling the unfiltered Flathub repository."
            ujust enable-flathub-unfiltered
            echo "Installing the Steam Flatpak package."
            flatpak install -y flathub com.valvesoftware.Steam
            echo "Disabling hardened_malloc for Steam to prevent compatibility issues."
            flatpak override --user --unset-env=LD_PRELOAD --nofilesystem=host-os com.valvesoftware.Steam
            ;;
        2)
            echo "Distrobox method selected."
            if [[ "$(ujust set-container-userns status)" == "disabled" ]]; then
                echo
                echo "Distrobox requires container domain user namespaces to work, which are disabled by default for security reasons."
                echo "You need to run 'ujust set-container-userns on' to allow this."
                read -rp "Would you like to run 'ujust set-container-userns on' now? [Y/n] " container_userns_now
                container_userns_now=${container_userns_now:-y}
                if [[ "$container_userns_now" == [Yy]* ]]; then
                    echo
                    echo "Running 'ujust set-container-userns on'"
                    echo
                    ujust set-container-userns on
                fi
            fi
            echo
            echo "Creating bazzite-arch distrobox..."
            echo
            distrobox-create --unshare-netns --nvidia --image ghcr.io/ublue-os/bazzite-arch --name bazzite-arch -Y
            echo
            echo "Exporting Steam from bazzite-arch distrobox..."
            echo
            distrobox-enter -n bazzite-arch -- distrobox-export --app steam
            echo
            ;;
    esac

    echo "The script will now prompt you to reboot your system to apply your changes."
    echo "If you refuse to proceed, the script will exit with a status code of 1, indicating an error."
    echo "The script itself will have worked, but Steam may cease to function properly until you reboot your computer."
    echo "It's fine not to reboot right now, as long as you reboot once before launching Steam for the first time."
    echo
    echo "Please save all your work and close all apps before proceeding."
    echo
    read -rp "Reboot now? [y/N] " reboot_now
    if [[ "$reboot_now" == [Yy]* ]]; then
        echo
        echo "The system will reboot now!"
        echo
        systemctl reboot
    else
        exit 1
    fi
