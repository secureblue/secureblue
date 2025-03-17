# vim: set ft=make :
# Copyright 2024 secureblue
#
# This file includes code from Universal Blue which is licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

uid := `id -u`
shell := `grep :$(id -u): /etc/passwd | cut -d: -f7`

# Boot into this device's BIOS/UEFI screen
bios:
    #!/usr/bin/bash
    if [ -d /sys/firmware/efi ]; then
      systemctl reboot --firmware-setup
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

# Regenerate GRUB config, useful in dual-boot scenarios where a second operating system isn't listed
regenerate-grub:
    #! /bin/run0 /bin/bash
    if [ -d /sys/firmware/efi ]; then
      grub2-mkconfig -o /etc/grub2-efi.cfg
    else
      grub2-mkconfig -o /etc/grub2.cfg
    fi

# Enroll Nvidia driver & KMOD signing key for secure boot - Enter password "universalblue" if prompted
enroll-secure-boot-key:
    #! /usr/bin/bash
    run0 mokutil --timeout -1
    echo 'The next line will prompt for a MOK password. Then, input "universalblue"'
    run0 mokutil --import /etc/pki/akmods/certs/akmods-ublue.der
    echo -e "At next reboot, the mokutil UEFI menu UI will be displayed (*QWERTY* keyboard input and navigation).\nThen, select "Enroll MOK", and input "universalblue" as the password"

# Toggle display of the user-motd in terminal
toggle-user-motd:
    #!/usr/bin/bash
    if test -e "${HOME}/.config/no-show-user-motd"; then
      rm -f "${HOME}/.config/no-show-user-motd"
    else
      if test ! -d "${HOME}/.config"; then
        mkdir "${HOME}/.config"
      fi
      touch "${HOME}/.config/no-show-user-motd"
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
    flatpak uninstall --unused
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

# Rerun Yafti
rerun-yafti:
    #!/usr/bin/bash
    yafti -f /usr/share/ublue-os/firstboot/yafti.yml

alias assemble := distrobox-assemble

# Create distroboxes from a defined manifest
distrobox-assemble CONTAINER="prompt" ACTION="create" FILE="/etc/distrobox/distrobox.ini":
    #!/usr/bin/bash
    if [[ "$(ujust check-container-userns-state)" == "disabled" ]]; then
        echo "Distrobox requires container domain user namespaces to work, which are disabled by default for security reasons."
        echo "You need to run 'ujust toggle-container-domain-userns-creation' to allow this."
        container_userns_now=""
        read -p "Would you like to run 'ujust toggle-container-domain-userns-creation' now? [Y/n] " container_userns_now
        container_userns_now=${container_userns_now:-y}
        if [[ "$container_userns_now" == [Yy]* ]]; then
            echo "Running 'ujust toggle-container-domain-userns-creation'"
            ujust toggle-container-domain-userns-creation
        fi
    fi
    # Distroboxes are gathered from distrobox.ini, please add them there
    source /usr/lib/ujust/ujust.sh
    AssembleList {{ FILE }} {{ ACTION }} {{ CONTAINER }}

# Create toolbox containers from a defined manifest (this spec will not be expanded)
toolbox-assemble CONTAINER="prompt" ACTION="create" FILE="/etc/toolbox/toolbox.ini":
    #!/usr/bin/bash
    if [[ "$(ujust check-container-userns-state)" == "disabled" ]]; then
        echo "Toolbox requires container domain user namespaces to work, which are disabled by default for security reasons."
        echo "You need to run 'ujust toggle-container-domain-userns-creation' to allow this."
        container_userns_now=""
        read -p "Would you like to run 'ujust toggle-container-domain-userns-creation' now? [Y/n] " container_userns_now
        container_userns_now=${container_userns_now:-y}
        if [[ "$container_userns_now" == [Yy]* ]]; then
            echo "Running 'ujust toggle-container-domain-userns-creation'"
            ujust toggle-container-domain-userns-creation
        fi
    fi
    # Toolboxes are gathered from toolbox.ini, please add them there
    source /usr/lib/ujust/ujust.sh
    ToolboxAssembleList {{ FILE }} {{ ACTION }} {{ CONTAINER }}

# Run a non-flatpak application with standard memory allocator (needs an argument!)
with-standard-malloc APP:
    #!/usr/bin/bash
    bwrap --dev-bind / / --ro-bind /dev/null /etc/ld.so.preload {{ APP }}

# Add the unfiltered Flathub flatpak repo
enable-flathub-unfiltered:
    #!/usr/bin/bash
    flatpak remote-add --if-not-exists --user flathub https://flathub.org/repo/flathub.flatpakrepo

# Returns the state of container domain user namespaces. (enabled/disabled)
check-container-userns-state:
    #!/usr/bin/bash
    set -euo pipefail
    podman unshare true &> /dev/null && echo 'enabled' || echo 'disabled'

# Returns the state of unconfined domain user namespaces. (enabled/disabled)
check-unconfined-userns-state:
    #!/usr/bin/bash
    set -euo pipefail
    unshare -U true &> /dev/null && echo 'enabled' || echo 'disabled'

# Install Steam via choice of 3 methods
install-steam:
    #!/usr/bin/bash
    if [ -z "$(pgrep Xwayland)" ] && [ -z "$(pgrep Xorg)" ] ; then
        echo "Steam requires X or Xwayland, which your variant of secureblue has disabled by default."
        echo "Please run 'ujust toggle-xwayland' to re-enable it."
        toggle_xwayland_now=""
        read -p "Would you like to run 'ujust toggle-xwayland' now? [Y/n] " toggle_xwayland_now
        toggle_xwayland_now=${toggle_xwayland_now:-y}
        if [[ "$toggle_xwayland_now" == [Yy]* ]]; then
            echo "Running 'ujust toggle-xwayland'"
            ujust toggle-xwayland
            reboot_now=""
            read -p "Would you like to reboot now? [y/N] " reboot_now
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
        read -p "Selection [1-2]: " method_selection
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
            ;;
        2)
            echo "Distrobox method selected."
            if [[ "$(ujust check-container-userns-state)" == "disabled" ]]; then
                echo "Distrobox requires container domain user namespaces to work, which are disabled by default for security reasons."
                echo "You need to run 'ujust toggle-container-domain-userns-creation' to allow this."
                container_userns_now=""
                read -p "Would you like to run 'ujust toggle-container-domain-userns-creation' now? [Y/n] " container_userns_now
                container_userns_now=${container_userns_now:-y}
                if [[ "$container_userns_now" == [Yy]* ]]; then
                    echo "Running 'ujust toggle-container-domain-userns-creation'"
                    ujust toggle-container-domain-userns-creation
                fi
            fi
            echo "Creating bazzite-arch distrobox."
            distrobox-create --unshare-netns --nvidia --image ghcr.io/ublue-os/bazzite-arch --name bazzite-arch -Y
            echo "Exporting Steam from bazzite-arch distrobox."
            distrobox-enter -n bazzite-arch -- distrobox-export --app steam
            ;;
    esac

    echo "Steam requires support for 32-bit processes/syscalls."
    if [ -n "$(rpm-ostree kargs | grep 'ia32_emulation=0')" ] ; then
        echo "This script will now remove the 'ia32_emulation=0' kernel argument."
        rpm-ostree kargs --delete-if-present="ia32_emulation=0"
    else
        echo "Do not set the 'ia32_emulation=0' kernel argument."
    fi

# Install the official docker packages
install-docker:
    #! /bin/run0 /bin/bash
    curl -Lo /etc/yum.repos.d/docker-ce.repo https://download.docker.com/linux/fedora/docker-ce.repo
    rpm-ostree refresh-md
    rpm-ostree install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Uninstall the official docker packages
uninstall-docker:
    #! /bin/run0 /bin/bash
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
    media_path="/run/media/$USER/"
    selabel="user_home_t"
    supported_fs=("ext2" "ext3" "ext4" "jfs" "xfs" "btrfs") # ref: https://wiki.gentoo.org/wiki/SELinux/FAQ#Can_I_use_SELinux_with_any_file_system.3F

    if [ -z "$( ls -A "$media_path" 2>&- )" ]; then
        echo "You don't have any drives mounted in \"$media_path\", aborting."
        exit 0
    fi
    echo "Warning: This will label your drives mounted on \"$media_path\" such that they are treated as an extension to your home directory. (You can select which ones to label)"
    echo 'If you do not want Trivalent to have access to these drives, do not proceed.'
    read -p 'Are you sure you want to do this? [y/N] ' warning_proceed
    if ! [[ "$warning_proceed" == [Yy]* ]]; then
        echo 'Aborting.'
        exit 0
    fi

    for dir in "$media_path"*/
    do
        echo
        if [[ "$dir" =~ "'" ]]; then
            echo "WARNING: Single quotes in drive labels are forbidden to avoid command execution, skipping drive \"$dir\"..."
            continue
        fi
        if [[ "$(stat -c '%U' "$dir")" != "$USER" ]]; then
            echo "Drive root folder is not owned by you, skipping drive \"$dir\"..."
            continue
        fi
        detected_fs="$(df -T "$dir" | awk '{print $2}' | sed -n 2p)"
        if ! printf "%s\n" "${supported_fs[@]}" | grep -Fxq "$detected_fs"; then
            echo "SELinux support is unknown for filesystem $detected_fs, skipping drive \"$dir\"..."
            continue
        fi
        read -p "Do you want to label \"$dir\"? [y/N] " proceed
        if ! [[ "$proceed" == [Yy]* ]]; then
            echo 'Skipping...'
            continue
        fi
        echo "Labeling drive mounted on \"$dir\" with $selabel"
        dir=${dir%*/} # remove trailing slash
        if ! run0 sh -c "semanage fcontext -a -t $selabel '$dir(/.*)?' && restorecon -r '$dir'"; then
            echo 'Execution failed, aborting.'
            exit 1
        fi
    done

    echo -e '\nDone.'

# Convenience utility for layering VPN provider packages
install-vpn:
    #!/usr/bin/bash
    set -euo pipefail

    # supported VPN providers and the security features they need disabled, separated by spaces (the names of the helper functions to be called)
    declare -A vpn_providers=(
        ["ivpn"]="" # TODO
        ["mullvad"]="notice_gui_only enable_unconfined_userns enable_xwayland"
        ["proton"]=""
    )

    # helper functions for disabling security features
    function enable_unconfined_userns() {
        if [[ "$(ujust check-unconfined-userns-state)" == "enabled" ]] ; then
            echo 'Unconfined domain user namespaces already enabled, skipping...'
            return
        fi
        echo 'This VPN requires unconfined domain user namespaces to be enabled.'
        echo 'This will execute "ujust toggle-unconfined-domain-userns-creation". You can also manually do this later if you skip this step.'
        echo 'Warning: This is a security reduction!'
        local proceed
        read -p 'Do you want to do this now? [Y/n] ' proceed
        if ! [[ "$proceed" == [nN]* ]]; then
            echo 'Enabling unconfined domain user namespaces...'
            ujust toggle-unconfined-domain-userns-creation
            echo 'Enabled unconfined domain user namespaces.'
        fi
    }
    function enable_xwayland() {
        local DE="unknown"
        local IMAGE="$(rpm-ostree status | grep '●')"
        if [ -n "$(echo "$IMAGE" | grep 'silverblue')" ] ; then
            DE=gnome
        elif [ -n "$(echo "$IMAGE" | grep 'kinoite')" ] ; then
            DE=plasma
        elif [ -n "$(echo "$IMAGE" | grep 'sericea')" ] || [ -n "$(echo "$IMAGE" | grep 'sway')" ] ; then
            DE=sway
        fi

        if [[ "$DE" == "unknown" ]]; then
            echo 'Warning: Unable to identify your desktop environment. Please manually ensure that XWayland is enabled. Skipping...'
            return
        fi

        local xwayland_enabled="0"
        if [ "$DE" == "gnome" ]; then
            GNOME_XWAYLAND_FILE="/etc/systemd/user/org.gnome.Shell@wayland.service.d/override.conf"
            if ! test -e $GNOME_XWAYLAND_FILE; then
                xwayland_enabled="1"
            fi
        elif [ "$DE" == "plasma" ]; then
            PLASMA_XWAYLAND_FILE="/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf"
            if ! test -e $PLASMA_XWAYLAND_FILE; then
                xwayland_enabled="1"
            fi
        elif [ "$DE" == "sway" ]; then
            SWAY_XWAYLAND_FILE="/etc/sway/config.d/99-noxwayland.conf"
            if ! test -e $SWAY_XWAYLAND_FILE; then
                xwayland_enabled="1"
            fi
        fi

        if [[ "$xwayland_enabled" == "1" ]]; then
            echo 'XWayland already enabled, skipping...'
            return
        fi

        echo 'This VPN requires XWayland to be enabled.'
        echo 'This will execute "ujust toggle-xwayland". You can also manually do this later if you skip this step.'
        echo 'Warning: This is a security reduction!'
        local proceed
        read -p 'Do you want to do this now? [Y/n] ' proceed
        if ! [[ "$proceed" == [nN]* ]]; then
            echo 'Enabling XWayland...'
            ujust toggle-xwayland
            echo 'Enabled XWayland.'
        fi
    }
    function notice_gui_only() {
        echo 'Notice: The following security features only need to be disabled if you intend on using the VPNs graphical user interface.'
        echo 'If you only intend on using the command-line interface, you can skip to the installation right away.'
        local proceed
        read -p 'Do you want to skip to the installation? [y/N] ' proceed
        if [[ "$proceed" == [yY]* ]]; then
            echo 'Skipping...'
            echo
            util_installvpn
        fi
    }

    # VPN install logic
    function install_ivpn() {
        true; # TODO
    }
    function install_mullvad() {
        local REPO_FILE="/etc/yum.repos.d/mullvad.repo"
        local REPO_URL="https://repository.mullvad.net/rpm/stable/mullvad.repo"

        if [ -a "$REPO_FILE" ]; then
            echo 'Warning: The Mullvad repofile does already exist. It will be overwritten if you continue.'
            local proceed
            read -p 'Are you sure you want to continue? [Y/n] ' proceed
            if [[ "$proceed" == [nN]* ]]; then
                echo 'Aborting...'
                exit 0
            fi
            echo 'Continuing...'
            echo
        fi

        if util_checkpackage "mullvad-vpn"; then
            echo 'Error: The package "mullvad-vpn" is already installed.'
            echo 'Aborting...'
            exit 1
        fi

        echo 'Installing Mullvad VPN...'
        # Notice: We're intentionally not enabling `mullvad-early-boot-blocking.service` --now, as that would block network.
        # It is intended to start on boot and then have it's restrictions lifted as soon as the daemon starts.
        if ! run0 sh -c "wget -O $REPO_FILE $REPO_URL && rpm-ostree install --assumeyes --apply-live mullvad-vpn && systemctl enable --now mullvad-daemon.service && systemctl enable mullvad-early-boot-blocking.service"; then
            echo "Error: The installation didn't complete successfully, aborting..."
            exit 1
        fi
        echo 'Successfully installed Mullvad VPN.'
    }
    function install_proton() {
        RPM_URL="https://repo.protonvpn.com/fedora-$(cat /etc/fedora-release | cut -d' ' -f 3)-stable/protonvpn-stable-release/protonvpn-stable-release-1.0.2-1.noarch.rpm"
        PACKAGE_NAME="proton-vpn-gnome-desktop"

        if util_checkpackage "$PACKAGE_NAME"; then
            echo "Error: the package \"$PACKAGE_NAME\" is already installed."
            echo 'Aborting...'
            exit 1
        fi

        if util_checkpackage "protonvpn-stable-release"; then
            echo 'Warning: It appears that the package "protonvpn-stable-release" (repository meta-package) is already installed, but Proton VPN is not.'
            local proceed
            read -p 'Do you want to continue? This will use the existing meta-package [Y/n] ' proceed
            if [[ "$proceed" == [nN]* ]]; then
                echo 'Aborting...'
                exit 0
            fi
            echo 'Continuing with existing meta-package...'
            echo
        else
            TMP_DIR="$(mktemp)"
            TMP_RPM="$TMP_DIR/protonvpn-metapackage.rpm"
            echo 'Installing meta-package...'
            if ! wget -O "$TMP_RPM" "$RPM_URL"; then
                echo 'Error: Failed to download meta-package, aborting...'
                exit 1
            fi
            if ! rpm-ostree install --assumeyes --apply-live "$TMP_RPM"; then
                echo 'Error: Failed to install meta-package, aborting...'
                exit 1
            fi
            echo 'Installed meta-package. Cleaning up...'
            rm "$TMP_RPM"
            rmdir "$TMP_DIR"
            echo 'Done.'
        fi

        echo
        echo 'Installing Proton VPN...'
        if ! rpm-ostree install --assumeyes "$PACKAGE_NAME"; then
            echo 'Error: Failed to install Proton VPN, aborting...'
            exit 1
        fi
        echo 'Successfully installed Proton VPN.'
    }

    function util_checkpackage() {
        rpm -qa | grep -q "$1"
        return $?
    }
    function util_installvpn() {
        echo 'Starting installation...'
        install_func="install_$vpn_choice"
        $install_func
        echo 'Please reboot your device to fully apply the changes.'
    }

    # script start
    echo 'WARNING: It is strongly recommended that you **not** use VPN provider desktop applications, as they generally require significant security downgrades.'
    echo 'Instead, it is recommended that you download wireguard profiles from your provider and import them into your desktop environment.'
    read -p 'If you understand this and still wish to continue, please type "SECURITY DOWNGRADE": ' security_downgrade
    if [[ "$security_downgrade" != "SECURITY DOWNGRADE" ]]; then
        echo 'Aborting...'
        exit 0
    fi
    echo
    valid_choice="0"
    while [[ "$valid_choice" == "0" ]]; do
        echo 'Please choose your desired provider:'
        vpn_choice="$(ugum choose "${!vpn_providers[@]}")"
        if [ -z ${vpn_providers["$vpn_choice"]+x} ]; then
            echo "Invalid provider choice: $vpn_choice. Please try again."
        else
            valid_choice="1"
        fi
    done
    echo "You selected $vpn_choice"
    install_func="install_$vpn_choice"
    IFS=' ' read -ra disable_hardening_arr <<< "${vpn_providers[$vpn_choice]}"
    for disable_hardening in "${disable_hardening_arr[@]}"; do
        echo
        $disable_hardening
    done
    echo
    util_installvpn
