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
    run0 mokutil --timeout -1
    echo 'The next line will prompt for a MOK password. Then, input "universalblue"'
    run0 mokutil --import /etc/pki/akmods/certs/akmods-ublue.der
    echo 'At next reboot, the mokutil UEFI menu UI will be displayed (*QWERTY* keyboard input and navigation).\nThen, select "Enroll MOK", and input "universalblue" as the password'

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
    yafti -f /usr/share/ublue-os/firstboot/yafti.yml

alias assemble := distrobox-assemble

# Create distroboxes from a defined manifest
distrobox-assemble CONTAINER="prompt" ACTION="create" FILE="/etc/distrobox/distrobox.ini":
    #!/usr/bin/bash
    # Distroboxes are gathered from distrobox.ini, please add them there
    source /usr/lib/ujust/ujust.sh
    AssembleList {{ FILE }} {{ ACTION }} {{ CONTAINER }}

# Create toolbox containers from a defined manifest (this spec will not be expanded)
toolbox-assemble CONTAINER="prompt" ACTION="create" FILE="/etc/toolbox/toolbox.ini":
    #!/usr/bin/bash
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

# search for an installed SELinux module
semodule-check MODULE:
    #! /bin/run0 /bin/bash
    if [ -n "$( semodule -l | grep {{ MODULE }} )" ] ; then
        semodule -l | grep {{ MODULE }}
    fi

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
            if [ -n "$(ujust semodule-check harden_container_userns)" ] ; then
                echo "Distrobox requires that secureblue's harden-container-userns module be disabled"
                echo "Please run 'ujust toggle-container-domain-userns-creation'"
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
