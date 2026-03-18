# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Install Steam via choice of 2 methods
install-steam:
    #!/usr/bin/bash
    need_reboot=false
    if [ -z "$(pgrep Xwayland)" ] && [ -z "$(pgrep Xorg)" ] ; then
        echo "Steam requires X or Xwayland, which your variant of secureblue has disabled by default." | fold -s
        echo "Please run 'ujust set-xwayland on' to re-enable it."
        enable_xwayland_now=""
        read -rp "Would you like to run 'ujust set-xwayland on' now? [Y/n] " enable_xwayland_now
        enable_xwayland_now=${enable_xwayland_now:-y}
        if [[ "$enable_xwayland_now" == [Yy]* ]]; then
            echo "Running 'ujust set-xwayland on'"
            ujust set-xwayland on
            need_reboot=true
        fi
    fi
    method_selection=""
    echo "Please select a method to install Steam:"
    echo "    1) Flatpak - Install the Steam flatpak from flathub-unverified (Recommended for most users)" | fold -s
    echo "    2) Distrobox - Install Steam via the steambox (bazzite-arch) distrobox image (Recommended for SteamVR users)" | fold -s
    while true; do
        read -rp "Selection (1 or 2): " method_selection
        case "$method_selection" in
            1|2) break ;;
            *) echo "That is not a valid selection." ;;
        esac
    done

    echo "" # blank space
    case "$method_selection" in
        1)
            echo "Flatpak method selected."
            if ! flatpak remotes --columns=name | grep -q '^flathub$'; then
                echo "The Steam flatpak is not verified by Valve and only distributed via the unfiltered Flathub repo." | fold -s
                read -rp "Would you like to enable the unfiltered Flathub repo now? [Y/n] " flathub_unfiltered
                flathub_unfiltered=${flathub_unfiltered:-y}
                if [[ "$flathub_unfiltered" == [Yy]* ]]; then
                    echo "Enabling the unfiltered Flathub repo."
                    ujust enable-flathub-unfiltered
                else
                    echo "The unfiltered Flathub repo is needed to install the Steam flatpak. Aborting."
                    exit 1
                fi
            fi
            echo "Installing Steam flatpak."
            flatpak install -y flathub com.valvesoftware.Steam
            echo "Disabling hardened_malloc for Steam."
            flatpak override --user --unset-env=LD_PRELOAD --nofilesystem=host-os com.valvesoftware.Steam

            echo "" # spaced out to be more obvious and for ease of reading
            echo "Granting Steam necessary permissions for basic functionality, including access to X11 and PulseAudio." | fold -s
            echo "This will override the flatpak-permissions-lockdown command, or any other global overrides." | fold -s
            echo "Note that to use controllers, you must additionally grant device=input if it is globally denied." | fold -s
            echo "Games with anti-cheats will likely require granting allow=devel alongside running ujust toggle-anticheat-support." | fold -s
            flatpak override --user --share=network --share=ipc --socket=x11 --socket=pulseaudio --allow=multiarch --allow=per-app-dev-shm com.valvesoftware.Steam
            echo ""
            ;;
        2)
            echo "Distrobox method selected."
            if [[ "$(ujust set-container-userns status)" == "disabled" ]]; then
                echo "Distrobox requires container domain user namespaces to work, which are disabled by default for security reasons." | fold -s
                echo "You need to run 'ujust set-container-userns on' to allow this."
                container_userns_now=""
                read -rp "Would you like to run 'ujust set-container-userns on' now? [Y/n] " container_userns_now
                container_userns_now=${container_userns_now:-y}
                if [[ "$container_userns_now" == [Yy]* ]]; then
                    echo "Running 'ujust set-container-userns on'"
                    ujust set-container-userns on
                fi
            fi
            echo "Creating steambox distrobox."
            distrobox-create --unshare-netns --nvidia --image ghcr.io/ublue-os/steambox --name steambox -Y
            echo "Exporting Steam from steambox distrobox."
            distrobox-enter -n steambox -- distrobox-export --app steam
            ;;
    esac

    echo "Steam requires support for 32-bit processes/syscalls."
    if rpm-ostree kargs | grep -q 'ia32_emulation=0'; then
        echo "This script will now remove the 'ia32_emulation=0' kernel argument."
        rpm-ostree kargs --delete-if-present="ia32_emulation=0"
        echo "Changing kernel arguments requires a reboot to take effect."
        echo "Reboot before running Steam."
        need_reboot=true
    fi
    echo "Remember: Steam requires 32-bit support; do not set the 'ia32_emulation=0' kernel argument."

    if [[ $(</proc/sys/kernel/yama/ptrace_scope) != 1 ]]; then
        echo "Some game anti-cheats require ptrace_scope set to 1."
        echo "You can change your ptrace_scope setting by running 'ujust toggle-anticheat-support'."
        toggle_anticheat=""
        read -rp "Would you like to set ptrace_scope to 1 now? [y/N] " toggle_anticheat
        if [[ "$toggle_anticheat" == [Yy]* ]]; then
            ujust toggle-anticheat-support
            need_reboot=true
        fi
    fi

    if [[ "$need_reboot" == true ]]; then
        echo "One or more of the changes made necessitates a reboot."
        echo "Steam will not work until you reboot."
        reboot_now=""
        read -rp "Would you like to reboot now? [y/N] " reboot_now
        if [[ "$reboot_now" == [Yy]* ]]; then
            echo "Rebooting"
            systemctl reboot
        fi
    fi
