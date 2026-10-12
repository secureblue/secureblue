# vim: set ft=make :
# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Clean up old up unused podman images, volumes, flatpak packages and rpm-ostree content
@clean-system:
    exec /usr/libexec/secureblue/clean-system

# Check for local overrides
@check-local-overrides:
    exec /usr/libexec/secureblue/check-local-overrides

alias assemble := distrobox-assemble

# Create distroboxes from a defined manifest
[positional-arguments]
@distrobox-assemble CONTAINER="prompt" ACTION="create" FILE="/etc/distrobox/distrobox.ini":
    exec /usr/libexec/secureblue/distrobox-assemble "$@"

# Create toolbox containers from a defined manifest (this spec will not be expanded)
[positional-arguments]
@toolbox-assemble CONTAINER="prompt" ACTION="create" FILE="/etc/toolbox/toolbox.ini":
    exec /usr/libexec/secureblue/toolbox-assemble "$@"

# Rebase to a different secureblue Desktop Environment/Atomic Desktop
@rebase-secureblue:
    exec /usr/libexec/secureblue/rebase-secureblue

# Apply SELinux type "user_home_t" on external drives to allow access from Trivalent
@label-external-drives:
    exec /usr/libexec/secureblue/label-external-drives

# Convenience utility for layering VPN provider packages
install-vpn:
    #!/usr/bin/bash
    set -euo pipefail

    if [[ ! -f "/usr/bin/rpm-ostree" ]]; then
        echo "Cannot layer packages on a UKI system. Try a systemd-sysext instead."
        exit 1
    fi

    # supported VPN providers and the security features they need disabled, separated by spaces
    declare -A vpn_providers=(
        ["ivpn"]="gui_needs_unconfined_userns"
        ["mullvad"]="gui_needs_unconfined_userns"
        ["proton"]=""
        ["tailscale"]=""
    )

    # VPN install logic
    # ref: https://www.ivpn.net/knowledgebase/linux/fedora-silverblue/
    # ref: https://mullvad.net/de/download/vpn/linux
    # ref: https://protonvpn.com/support/en/official-linux-vpn-fedora
    function install_vpn() {
        local INSTRUCTIONS
        local PACKAGE_NAMES
        local REPO_NAME
        case "$1" in
            "ivpn")
                PACKAGE_NAMES="ivpn"
                REPO_NAME="${PACKAGE_NAMES}"

                if util_checkpackage "${PACKAGE_NAMES}" || util_checkpackage "${PACKAGE_NAMES}-ui"; then
                    echo 'Error: IVPN is already installed.'
                    echo 'Aborting...'
                    exit 1
                fi

                echo 'Installing IVPN...'
                local proceed2
                read -rp 'Do you want the IVPN GUI to be installed? [Y/n] ' proceed2
                if ! [[ "${proceed2}" == [nN]* ]]; then
                    PACKAGE_NAMES="${PACKAGE_NAMES} ${PACKAGE_NAMES}-ui"
                fi
                INSTRUCTIONS='Successfully installed IVPN. Please execute the command "systemctl enable --now ivpn-service" after rebooting.'
                ;;

            "mullvad")
                PACKAGE_NAMES="mullvad-vpn"
                REPO_NAME="mullvad"

                if util_checkpackage "${PACKAGE_NAMES}"; then
                    echo 'Error: Mullvad VPN is already installed.'
                    echo 'Aborting...'
                    exit 1
                fi

                echo 'Installing Mullvad VPN...'
                INSTRUCTIONS='Successfully installed Mullvad VPN. Please execute the command "systemctl enable --now mullvad-daemon && systemctl enable mullvad-early-boot-blocking" after rebooting.'
                ;;

            "proton")
                PACKAGE_NAMES="proton-vpn-gnome-desktop"
                REPO_NAME="protonvpn-stable"

                if util_checkpackage "${PACKAGE_NAMES}"; then
                    echo 'Error: Proton VPN is already installed.'
                    echo 'Aborting...'
                    exit 1
                fi

                echo 'Installing Proton VPN...'
                INSTRUCTIONS='Successfully installed Proton VPN.'
                ;;

            "tailscale")
                PACKAGE_NAMES="tailscale"
                REPO_NAME="tailscale"

                if util_checkpackage "${PACKAGE_NAMES}"; then
                    echo 'Error: Tailscale VPN is already installed.'
                    echo 'Aborting...'
                    exit 1
                fi

                echo 'Installing Tailscale VPN...'
                INSTRUCTIONS='Successfully installed Tailscale VPN, please execute the command "run0 systemctl enable --now tailscaled && run0 tailscale up".'
                ;;

            *)
                echo 'Invalid choice'
                exit 1
                ;;

        esac

        # The lack of quotes around $2 is intentional.
        # shellcheck disable=SC2086
        if ! run0 sh -c 'sed -Ei "s/^enabled[[:space:]]*=.*/enabled=1/" "/usr/share/dnf5/repos.d/$1.repo" && rpm-ostree install -y $2' sh "${REPO_NAME}" "${PACKAGE_NAMES}"; then
            echo "Error: The installation didn't complete successfully, aborting..."
            exit 1
        fi

        echo "${INSTRUCTIONS}"
    }

    function util_checkpackage() {
        rpm -qa | grep -q "$1"
        return $?
    }

    # script start
    echo 'Using a VPN is currently incompatible with global DNS or local DNSSEC resolution.'
    echo 'If you are using Unbound, it will be disabled in favour of systemd-resolved.'
    read -rp 'Do you want to continue? [y/N] ' proceed
    if ! [[ "${proceed}" == [yY]* ]]; then
        echo 'Aborting...'
        exit 0
    fi
    echo

    echo 'NOTE: You can also install wireguard profiles from your provider directly into your DE, if you prefer.'
    read -rp 'Do you want to continue with installing a VPN app anyway? [y/N] ' proceed
    if ! [[ "${proceed}" == [yY]* ]]; then
        echo 'Aborting...'
        exit 0
    fi
    echo
    echo 'Please choose your desired provider'
    vpn_choice="$(ugum choose "${!vpn_providers[@]}")"
    echo "You selected ${vpn_choice}"

    vpn_requirements="${vpn_providers[${vpn_choice}]}"
    needs_gui="1"
    if [[ "${vpn_requirements}" =~ "gui_needs_" ]]; then
        echo
        echo 'Notice: This VPN requires additional security features to be disabled in order to use its graphical interface.'
        echo "You can instead use the VPN app's command-line interface, which does not require disabling hardening."
        read -rp 'Do you intend to use the graphical interface? [y/N] ' proceed_gui
        if [[ "${proceed_gui}" == [yY]* ]]; then
            echo 'Additional hardening features that break the graphical interface will be disabled.'
        else
            echo 'Additional hardening features that break the graphical interface will not be disabled.'
            needs_gui="0"
        fi
    fi

    if [[ "${vpn_requirements}" =~ "always_needs_unconfined_userns" || "${vpn_requirements}" =~ "gui_needs_unconfined_userns" && "${needs_gui}" == "1" ]]; then
        echo
        if [[ "$(ujust set-unconfined-userns status)" == "enabled" ]] ; then
            echo 'Unconfined domain user namespaces already enabled, skipping...'
        else
            echo 'This VPN requires unconfined domain user namespaces to be enabled.'
            echo 'This will execute "ujust set-unconfined-userns on". You can also manually do this later if you skip this step.'
            echo 'Warning: This is a security reduction!'
            read -rp 'Do you want to do this now? [Y/n] ' proceed_userns
            if ! [[ "${proceed_userns}" == [nN]* ]]; then
                echo 'Enabling unconfined domain user namespaces...'
                ujust set-unconfined-userns on
                echo 'Enabled unconfined domain user namespaces.'
            fi
        fi
    fi

    if [[ "${vpn_requirements}" =~ "always_needs_xwayland" || "${vpn_requirements}" =~ "gui_needs_xwayland" && "${needs_gui}" == "1" ]]; then
        echo

        DE="unknown"
        IMAGE="$(rpm-ostree status 2>&- | grep '●')"
        if echo "${IMAGE}" | grep -q 'silverblue'; then
            DE="gnome"
        elif echo "${IMAGE}" | grep -q 'kinoite'; then
            DE="plasma"
        elif echo "${IMAGE}" | grep -q 'sericea' || echo "${IMAGE}" | grep 'sway'; then
            DE=sway
        fi

        xwayland_enabled="0"
        if [[ "${DE}" == "gnome" ]]; then
            if ! test -e "/etc/systemd/user/org.gnome.Shell@user.service.d/override.conf"; then
                xwayland_enabled="1"
            fi
        elif [[ "${DE}" == "plasma" ]]; then
            if ! test -e "/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf"; then
                xwayland_enabled="1"
            fi
        elif [[ "${DE}" == "sway" ]]; then
            if ! test -e "/etc/sway/config.d/99-noxwayland.conf"; then
                xwayland_enabled="1"
            fi
        fi

        if [[ "${DE}" == "unknown" ]]; then
            echo 'Warning: Unable to identify your desktop environment. Please manually ensure that Xwayland is enabled. Skipping...'
        elif [[ "${xwayland_enabled}" == "1" ]]; then
            echo 'Xwayland already enabled, skipping...'
        else
            echo 'This VPN requires Xwayland to be enabled.'
            echo 'This will execute "ujust set-xwayland on". You can also manually do this later if you skip this step.'
            echo 'Warning: This is a security reduction!'
            read -rp 'Do you want to do this now? [Y/n] ' proceed_xwayland
            if ! [[ "${proceed_xwayland}" == [nN]* ]]; then
                echo 'Enabling Xwayland...'
                ujust set-xwayland on
                echo 'Enabled Xwayland.'
            fi
        fi
    fi

    # Switch DNS resolver to systemd-resolved if this isn't already set.
    echo
    resolver=$(
        /usr/libexec/secureblue/dns_selector.py status |
        sed -n 's/^DNS Resolver: //p'
    )
    if [[ "${resolver}" == "systemd-resolved" ]]; then
        echo 'DNS resolver is already systemd-resolved. Continuing...'
    else
        echo "Detected DNS resolver as ${resolver}".
        echo 'Setting DNS resolver to systemd-resolved...'
        /usr/libexec/secureblue/dns_selector.py resolver resolved > /dev/null
    fi

    echo
    echo 'Starting installation...'
    install_vpn "${vpn_choice}"
    echo 'Please reboot your device to fully apply the changes.'

# Setup USBGuard
@setup-usbguard:
    exec /usr/libexec/secureblue/setup-usbguard
