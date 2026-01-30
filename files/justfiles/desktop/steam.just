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
        need_reboot=true
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
            need_reboot=true
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
            need_reboot=true
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

            echo
            echo "When using Steam via Flatpak in a hardened Flatpak environment, Steam needs access to some restricted systems in order to ensure proper functionality."
            echo "If you proceed, this will give Steam access to some system functionality, including access X11 and PulseAudio."
            echo "This will override the 'flatpak-permissions-lockdown' command, or any other global overrides (for the Steam Flatpak only)."
            echo "Note that to use controllers you must additionally grant the 'device=input' and 'allow=bluetooth' (for wireless controller support) permissions if they are globally denied."
            echo "Games with anti-cheats will likely require granting 'allow=devel' alongside running 'ujust toggle-anticheat-support'."
            echo

            steam_flatpak_overrides_general="flatpak override --user --share=network --share=ipc --socket=x11 --socket=pulseaudio --allow=multiarch --allow=per-app-dev-shm com.valvesoftware.Steam"
            steam_flatpak_overrides_ac="flatpak override --user --allow=devel com.valvesoftware.Steam"
            steam_flatpak_overrides_input="flatpak override --user --device=input com.valvesoftware.Steam"
            steam_flatpak_overrides_input_wireless="flatpak override --user --allow=bluetooth com.valvesoftware.Steam"

            echo "General overrides — Command to be run:"
            echo
            echo "${steam_flatpak_overrides_general}"
            echo
            # If the user skips general overrides, all subsequent Flatpak overrides are skipped as well
            read -rp "Proceed with applying general overrides? (RECOMMENDED) [Y/n]" apply_steam_overrides_general
            apply_steam_overrides_general=${apply_steam_overrides_general:-y}
            if [[ "$apply_steam_overrides_general" == [Yy]* ]]; then
            echo "Applying general Steam Flatpak overrides..."
            eval "$(steam_flatpak_overrides_general)"

                if [[ "$(sysctl -n kernel.yama.ptrace_scope)" = "1" ]]; then
                echo
                echo "Anti-cheat support seems to be enabled system-wide. Flatpak Steam needs 'allow=devel' to make processs tracing work as expected, which is required by anti-cheat solutions."
                echo
                echo "Anti-cheat override — Command to be run:"
                echo
                echo "${steam_flatpak_overrides_ac}"
                echo
                # Note that this will only run if the user has enabled support system-wide first, so it will not blindly ask to enable ptrace support
                read -rp "Grant the Steam Flatpak access to process tracing? (RECOMMENDED) [Y/n]" apply_steam_overrides_ac
                apply_steam_overrides_ac=${apply_steam_overrides_ac:-y}
                if [[ "$apply_steam_overrides_ac" == [Yy]* ]]; then
                echo "Applying anti-cheat override for the Steam Flatpak..."
                eval "$(steam_flatpak_overrides_ac)"
                fi
                else
                echo "Anti-cheat support is not enabled system-wide. The script will not grant the 'allow=devel' permission to the Steam Flatpak."
                fi

                echo
                echo "Input overrides — Command to be run:"
                echo
                echo "${steam_flatpak_overrides_input}"
                echo
                read -rp "Grant the Steam Flatpak access to joysticks and game controllers? [y/N]" apply_steam_overrides_input
                if [[ "$apply_steam_overrides_input" == [Yy]* ]]; then
                echo "Applying joystick override for the Steam Flatpak..."
                eval "$(steam_flatpak_overrides_input)"
                steam_joystick_applied=true
                fi

                    if [[ "${steam_joystick_applied}" == "true" ]]; then
                    echo "Wireless controller support — Command to be run:"
                    echo
                    echo "${steam_flatpak_overrides_input_wireless}"
                    echo
                    read -rp "Also grant the Steam Flatpak access to wireless controllers? [y/N]" apply_steam_overrides_input_wireless
                    if [[ "$apply_steam_overrides_input_wireless" == [Yy]* ]]; then
                    echo "Applying joystick override for the Steam Flatpak..."
                    eval "$(steam_flatpak_overrides_input_wireless)"
                    fi
                    fi

            fi
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

    if [[ ${need_reboot} == "true" ]]; then
    echo "A reboot is required for Steam to function properly."
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
    else
    echo Done. Everything is ready!
    fi
