# vim: set ft=make :
# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

uid := `id -u`
shell := `grep :$(id -u): /etc/passwd | cut -d: -f7`

# Boot into this device's BIOS/UEFI screen
bios:
    #!/usr/bin/bash
    if [ -d /sys/firmware/efi ]; then
      read -rp 'The system will reboot into UEFI firmware settings. Proceed? (y/N) ' proceed
      if [[ "$proceed" == [Yy]* ]]; then
        systemctl reboot --firmware-setup
      fi
    else
      echo "Rebooting to legacy BIOS from OS is not supported."
    fi

# Show all messages from this boot
logs-this-boot:
    #! /bin/run0 /bin/bash
    journalctl -b 0

# Show all messages from last boot
logs-last-boot:
    #! /bin/run0 /bin/bash
    journalctl -b -1

# Enroll secureblue's signing key for secure boot - Enter password "secureblue" if prompted
enroll-secureblue-secure-boot-key:
    #! /bin/run0 /bin/bash
    mokutil --timeout -1
    echo 'The next line will prompt for a MOK password. Input "secureblue".'
    mokutil --import /etc/pki/akmods/certs/akmods-secureblue.der
    echo 'At next reboot, the mokutil UEFI menu UI will be displayed (*QWERTY* keyboard input and navigation).'
    echo 'Then, select "Enroll MOK", and input "secureblue" as the password.'

# Update system (with provenance verification)
update-system:
    #!/bin/sh
    set -eu
    /usr/libexec/secureblue/verify-provenance.sh
    /usr/bin/rpm-ostree upgrade
    if [ -f /usr/libexec/secureblue/security-update-notification ]; then
        /usr/libexec/secureblue/security-update-notification >/dev/null 2>&1 &
    fi

# Update device firmware
[no-exit-message]
update-firmware:
    #!/usr/bin/bash
    fwupdmgr refresh --force
    fwupdmgr get-updates
    fwupdmgr update

# Clean up old up unused podman images, volumes, flatpak packages and rpm-ostree content
clean-system:
    #!/usr/bin/bash
    podman image prune -af
    podman volume prune -f
    if command -v flatpak &> /dev/null
    then
        flatpak uninstall --unused
    fi
    rpm-ostree cleanup -bm

# Check for local overrides
check-local-overrides:
    #!/usr/bin/bash
    diff -r \
      --suppress-common-lines \
      --color="always" \
      --exclude "passwd*" \
      --exclude "group*" \
      --exclude="subgid*" \
      --exclude="subuid*" \
      --exclude="machine-id" \
      --exclude="adjtime" \
      --exclude="fstab" \
      --exclude="system-connections" \
      --exclude="shadow*" \
      --exclude="gshadow*" \
      --exclude="ssh_host*" \
      --exclude="cmdline" \
      --exclude="crypttab" \
      --exclude="hostname" \
      --exclude="localtime" \
      --exclude="locale*" \
      --exclude="*lock" \
      --exclude=".updated" \
      --exclude="*LOCK" \
      --exclude="vconsole*" \
      --exclude="00-keyboard.conf" \
      --exclude="grub" \
      --exclude="system.control*" \
      --exclude="cdi" \
      --exclude="default.target" \
      /usr/etc /etc 2>/dev/null | sed '/Binary\ files\ /d'

# Debug dump pastebin for issue reporting
debug-info:
    #!/usr/bin/bash
    rpm_ostree_status=$(echo -e "=== Rpm-Ostree Status ===\n"; rpm-ostree status --verbose)
    sysinfo=$(echo -e "\n"; fpaste --sysinfo --printonly)
    flatpaks=$(echo "=== Flatpaks Installed ==="; flatpak list --columns=application,version,options)
    audit_results=$(echo -e "\n=== Audit Results ===\n"; ujust audit-secureblue)
    local_overrides=$(echo -e "\n=== Listing Local Overrides ===\n"; ujust check-local-overrides)
    recent_events=$(echo -e "\n=== Recent System Events ===\n"; journalctl -b -p err..alert --since "1 hour ago")
    failed_services=$(echo -e "\n=== Failed Services ===\n"; systemctl list-units --state=failed)
    content="$rpm_ostree_status$sysinfo$flatpaks$audit_results$local_overrides$recent_events$failed_services"
    echo "$content" | fpaste --confirm --private=1

alias assemble := distrobox-assemble

# Create distroboxes from a defined manifest
distrobox-assemble CONTAINER="prompt" ACTION="create" FILE="/etc/distrobox/distrobox.ini":
    #!/usr/bin/bash
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
    # Distroboxes are gathered from distrobox.ini, please add them there
    source /usr/lib/ujust/ujust.sh
    AssembleList "{{ FILE }}" "{{ ACTION }}" "{{ CONTAINER }}"

# Create toolbox containers from a defined manifest (this spec will not be expanded)
toolbox-assemble CONTAINER="prompt" ACTION="create" FILE="/etc/toolbox/toolbox.ini":
    #!/usr/bin/bash
    if [[ "$(ujust set-container-userns status)" == "disabled" ]]; then
        echo "Toolbox requires container domain user namespaces to work, which are disabled by default for security reasons."
        echo "You need to run 'ujust set-container-userns on' to allow this."
        container_userns_now=""
        read -rp "Would you like to run 'ujust set-container-userns on' now? [Y/n] " container_userns_now
        container_userns_now=${container_userns_now:-y}
        if [[ "$container_userns_now" == [Yy]* ]]; then
            echo "Running 'ujust set-container-userns on'"
            ujust set-container-userns on
        fi
    fi
    # Toolboxes are gathered from toolbox.ini, please add them there
    source /usr/lib/ujust/ujust.sh
    ToolboxAssembleList "{{ FILE }}" "{{ ACTION }}" "{{ CONTAINER }}"

# Install the official docker packages
install-docker:
    #! /bin/run0 /bin/bash
    set -euo pipefail
    tempfile=$(mktemp)
    curl -fLo "$tempfile" https://download.docker.com/linux/fedora/docker-ce.repo
    mv "$tempfile" /etc/yum.repos.d/docker-ce.repo
    rpm-ostree refresh-md
    rpm-ostree install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Uninstall the official docker packages
uninstall-docker:
    #! /bin/run0 /bin/bash
    set -euo pipefail
    rm /etc/yum.repos.d/docker-ce.repo
    rpm-ostree refresh-md
    rpm-ostree uninstall docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Rebase to a different secureblue Desktop Environment/Atomic Desktop
rebase-secureblue:
    #!/usr/bin/bash
    /usr/bin/bash /usr/share/secureblue/install_secureblue.sh

# Apply SELinux type "user_home_t" on external drives to allow access from Trivalent
label-external-drives:
    #!/usr/bin/bash
    set -euo pipefail
    media_paths=("/run/media/$USER/" "/mnt/")
    selabel="user_home_t"
    supported_fs=("ext2" "ext3" "ext4" "jfs" "xfs" "btrfs") # ref: https://wiki.gentoo.org/wiki/SELinux/FAQ#Can_I_use_SELinux_with_any_file_system.3F

    echo "Warning: This will label your drives mounted on paths $(printf '"%s" and ' "${media_paths[@]}" | sed 's/ and $//') such that they are treated as an extension to your home directory. (You can select which ones to label)"
    echo 'If you do not want Trivalent to have access to these drives, do not proceed.'
    read -rp 'Are you sure you want to do this? [y/N] ' warning_proceed
    if ! [[ "$warning_proceed" == [Yy]* ]]; then
        echo 'Aborting.'
        exit 0
    fi

    for media_path in "${media_paths[@]}"; do
        if [ -z "$( ls -A "$media_path" 2>&- )" ]; then
            echo
            echo "You don't have any drives mounted in \"$media_path\", skipping..."
            continue
        fi

        for dir in "$media_path"*/
        do
            echo
            if [[ "$(stat -c '%U' "$dir")" != "$USER" ]]; then
                echo "Drive root folder is not owned by you, skipping drive \"$dir\"..."
                continue
            fi
            detected_fs="$(df -T "$dir" | awk '{print $2}' | sed -n 2p)"
            if ! printf "%s\n" "${supported_fs[@]}" | grep -Fxq "$detected_fs"; then
                echo "SELinux support is unknown for filesystem $detected_fs, skipping drive \"$dir\"..."
                continue
            fi
            read -rp "Do you want to label \"$dir\"? [y/N] " proceed
            if ! [[ "$proceed" == [Yy]* ]]; then
                echo 'Skipping...'
                continue
            fi
            echo "Labeling drive mounted on \"$dir\" with $selabel"
            dir=${dir%*/} # remove trailing slash
            if ! run0 sh -c 'semanage fcontext -a -t "$1" "$2(/.*)?" && restorecon -r "$2"' sh "$selabel" "$dir"; then
                echo 'Execution failed, aborting.'
                exit 1
            fi
        done
    done

    echo -e '\nDone.'

# Convenience utility for layering VPN provider packages
install-vpn:
    #!/usr/bin/bash
    set -euo pipefail

    # supported VPN providers and the security features they need disabled, separated by spaces
    declare -A vpn_providers=(
        ["ivpn"]="gui_needs_unconfined_userns gui_needs_xwayland"
        ["mullvad"]="gui_needs_unconfined_userns gui_needs_xwayland"
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
                REPO_NAME="$PACKAGE_NAMES"

                if util_checkpackage "$PACKAGE_NAMES" || util_checkpackage "$PACKAGE_NAMES-ui"; then
                    echo 'Error: IVPN is already installed.'
                    echo 'Aborting...'
                    exit 1
                fi

                echo 'Installing IVPN...'
                local proceed2
                read -rp 'Do you want the IVPN GUI to be installed? [Y/n] ' proceed2
                if ! [[ "$proceed2" == [nN]* ]]; then
                    PACKAGE_NAMES="$PACKAGE_NAMES $PACKAGE_NAMES-ui"
                fi
                INSTRUCTIONS='Successfully installed IVPN. Please execute the command "systemctl enable --now ivpn-service" after rebooting.'
                ;;

            "mullvad")
                PACKAGE_NAMES="mullvad-vpn"
                REPO_NAME="mullvad"

                if util_checkpackage "$PACKAGE_NAMES"; then
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

                if util_checkpackage "$PACKAGE_NAMES"; then
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

                if util_checkpackage "$PACKAGE_NAMES"; then
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
        if ! run0 sh -c 'sed -Ei "s/^enabled[[:space:]]*=.*/enabled=1/" "/etc/yum.repos.d/$1.repo" && rpm-ostree install -y $2' sh "$REPO_NAME" "$PACKAGE_NAMES"; then
            echo "Error: The installation didn't complete successfully, aborting..."
            exit 1
        fi

        echo "$INSTRUCTIONS"
    }

    function util_checkpackage() {
        rpm -qa | grep -q "$1"
        return $?
    }

    # script start
    echo 'Using a VPN is currently incompatible with global DNS or local DNSSEC resolution.'
    echo 'If you are using Unbound, it will be disabled in favour of systemd-resolved.'
    read -rp 'Do you want to continue? [y/N] ' proceed
    if ! [[ "$proceed" == [yY]* ]]; then
        echo 'Aborting...'
        exit 0
    fi
    echo

    echo 'NOTE: You can also install wireguard profiles from your provider directly into your DE, if you prefer.'
    read -rp 'Do you want to continue with installing a VPN app anyway? [y/N] ' proceed
    if ! [[ "$proceed" == [yY]* ]]; then
        echo 'Aborting...'
        exit 0
    fi
    echo
    echo 'Please choose your desired provider'
    vpn_choice="$(ugum choose "${!vpn_providers[@]}")"
    echo "You selected $vpn_choice"

    vpn_requirements="${vpn_providers[$vpn_choice]}"
    needs_gui="1"
    if [[ "$vpn_requirements" =~ "gui_needs_" ]]; then
        echo
        echo 'Notice: This VPN requires additional security features to be disabled in order to use its graphical interface.'
        echo 'You can instead use the VPN app's command-line interface, which does not require disabling hardening.'
        read -rp 'Do you intend to use the graphical interface? [y/N] ' proceed_gui
        if [[ "$proceed_gui" == [yY]* ]]; then
            echo 'Additional hardening features that break the graphical interface will be disabled.'
        else
            echo 'Additional hardening features that break the graphical interface will not be disabled.'
            needs_gui="0"
        fi
    fi

    if [[ "$vpn_requirements" =~ "always_needs_unconfined_userns" || "$vpn_requirements" =~ "gui_needs_unconfined_userns" && "$needs_gui" == "1" ]]; then
        echo
        if [[ "$(ujust set-unconfined-userns status)" == "enabled" ]] ; then
            echo 'Unconfined domain user namespaces already enabled, skipping...'
        else
            echo 'This VPN requires unconfined domain user namespaces to be enabled.'
            echo 'This will execute "ujust set-unconfined-userns on". You can also manually do this later if you skip this step.'
            echo 'Warning: This is a security reduction!'
            read -rp 'Do you want to do this now? [Y/n] ' proceed_userns
            if ! [[ "$proceed_userns" == [nN]* ]]; then
                echo 'Enabling unconfined domain user namespaces...'
                ujust set-unconfined-userns on
                echo 'Enabled unconfined domain user namespaces.'
            fi
        fi
    fi

    if [[ "$vpn_requirements" =~ "always_needs_xwayland" || "$vpn_requirements" =~ "gui_needs_xwayland" && "$needs_gui" == "1" ]]; then
        echo

        DE="unknown"
        IMAGE="$(rpm-ostree status 2>&- | grep '●')"
        if echo "$IMAGE" | grep -q 'silverblue'; then
            DE="gnome"
        elif echo "$IMAGE" | grep -q 'kinoite'; then
            DE="plasma"
        elif echo "$IMAGE" | grep -q 'sericea' || echo "$IMAGE" | grep 'sway'; then
            DE=sway
        fi

        xwayland_enabled="0"
        if [[ "$DE" == "gnome" ]]; then
            if ! test -e "/etc/systemd/user/org.gnome.Shell@wayland.service.d/override.conf"; then
                xwayland_enabled="1"
            fi
        elif [[ "$DE" == "plasma" ]]; then
            if ! test -e "/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf"; then
                xwayland_enabled="1"
            fi
        elif [[ "$DE" == "sway" ]]; then
            if ! test -e "/etc/sway/config.d/99-noxwayland.conf"; then
                xwayland_enabled="1"
            fi
        fi

        if [[ "$DE" == "unknown" ]]; then
            echo 'Warning: Unable to identify your desktop environment. Please manually ensure that Xwayland is enabled. Skipping...'
        elif [[ "$xwayland_enabled" == "1" ]]; then
            echo 'Xwayland already enabled, skipping...'
        else
            echo 'This VPN requires Xwayland to be enabled.'
            echo 'This will execute "ujust set-xwayland on". You can also manually do this later if you skip this step.'
            echo 'Warning: This is a security reduction!'
            read -rp 'Do you want to do this now? [Y/n] ' proceed_xwayland
            if ! [[ "$proceed_xwayland" == [nN]* ]]; then
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
    if [[ "$resolver" == "systemd-resolved" ]]; then
        echo 'DNS resolver is already systemd-resolved. Continuing...'
    else
        echo "Detected DNS resolver as $resolver".
        echo 'Setting DNS resolver to systemd-resolved...'
        /usr/libexec/secureblue/dns_selector.py resolver resolved > /dev/null
    fi

    echo
    echo 'Starting installation...'
    install_vpn "$vpn_choice"
    echo 'Please reboot your device to fully apply the changes.'

# Setup USBGuard
setup-usbguard:
    #!/usr/bin/bash
    echo "Notice: This will generate a policy based on your existing connected USB devices."
    # shellcheck disable=SC2016
    run0 sh -c '
        mkdir -p /var/log/usbguard
        mkdir -p /etc/usbguard
        chmod 755 /etc/usbguard
        groupadd usbguard
        usermod -aG usbguard "$SUDO_USER"
        usbguard generate-policy > /etc/usbguard/rules.conf
        sed -i "/^IPCAllowedGroups=wheel/s/\$/ usbguard/" /etc/usbguard/usbguard-daemon.conf
        restorecon -vR /var/log/usbguard
        systemctl enable --now usbguard.service
        usbguard add-user "$SUDO_USER"
    '
    if ! rpm-ostree status | grep '●' | grep -Eq 'securecore|iot'; then
        systemctl enable --user --now usbguard-notifier.service
    fi
