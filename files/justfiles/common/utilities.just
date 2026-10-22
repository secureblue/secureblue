# vim: set ft=make :
# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Clean up old up unused podman images, volumes, flatpak packages and rpm-ostree content
clean-system:
    #!/usr/bin/bash
    podman image prune -af
    podman volume prune
    if command -v flatpak &> /dev/null
    then
        flatpak uninstall --unused
    fi
    if [[ -f "/usr/bin/rpm-ostree" ]]; then
        rpm-ostree cleanup -bm
    fi

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
        /usr/share/secureblue/etc /etc 2>/dev/null | sed '/Binary\ files\ /d'

# Debug dump pastebin for issue reporting
debug-info:
    #!/usr/bin/bash
    if [[ -f "/usr/bin/rpm-ostree" ]]; then
        rpm_ostree_status=$(echo -e "=== Rpm-Ostree Status ===\n"; rpm-ostree status --verbose)
    else
        echo "Please authenticate yourself as an administrator to collect debug info."
        rpm_ostree_status=$(echo -e "=== Bootc Status ===\n"; run0 -i bootc status --verbose)
    fi
    sysinfo=$(echo -e "\n"; fpaste --sysinfo --printonly)
    flatpaks=$(echo "=== Flatpaks Installed ==="; flatpak list --columns=application,version,options)
    audit_results=$(echo -e "\n=== Audit Results ===\n"; ujust audit-secureblue)
    local_overrides=$(echo -e "\n=== Listing Local Overrides ===\n"; ujust check-local-overrides)
    recent_events=$(echo -e "\n=== Recent System Events ===\n"; journalctl -b -p err..alert --since "1 hour ago")
    failed_services=$(echo -e "\n=== Failed Services ===\n"; systemctl list-units --state=failed)
    content="${rpm_ostree_status}${sysinfo}${flatpaks}${audit_results}${local_overrides}${recent_events}${failed_services}"
    echo "${content}" | fpaste --confirm --private=1

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
        if [[ "${container_userns_now}" == [Yy]* ]]; then
            echo "Running 'ujust set-container-userns on'"
            ujust set-container-userns on
        fi
    fi
    # Distroboxes are gathered from distrobox.ini, please add them there
    # shellcheck disable=SC1091
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
        if [[ "${container_userns_now}" == [Yy]* ]]; then
            echo "Running 'ujust set-container-userns on'"
            ujust set-container-userns on
        fi
    fi
    # Toolboxes are gathered from toolbox.ini, please add them there
    # shellcheck disable=SC1091
    source /usr/lib/ujust/ujust.sh
    ToolboxAssembleList "{{ FILE }}" "{{ ACTION }}" "{{ CONTAINER }}"

# Rebase to a different secureblue Desktop Environment/Atomic Desktop
rebase-secureblue:
    #!/usr/bin/bash
    set -euo pipefail
    current_image=$(grep VARIANT= /etc/os-release | cut -d'"' -f2)
    if [[ "${current_image}" == 'CoreOS' ]] || [[ "${current_image}" == 'IOT' ]]; then
        image_name=$(grep VARIANT_ID= /etc/os-release | cut -d'=' -f2 | cut -d'-' -f1)
        read -rp "Do you need ZFS support? [y/N]: " use_zfs
        [[ "${use_zfs}" == [Yy]* ]] && image_name+="-zfs"
    else
        desktop_image_types=(
            "silverblue"
            "kinoite"
            "sericea"
            "cosmic"
        )
        printf "%s\n" \
            "Select a desktop." \
            "Silverblue and Kinoite images are recommended." \
            "Sericea images are recommended for tiling WM users." \
            "Cosmic images are considered beta."
        PS3=$'Enter your desktop choice: '
        select image_name in "${desktop_image_types[@]}"; do
            if [[ -n "${image_name}" ]]; then
                echo "Selected desktop: ${image_name}"
                break
            else
                echo "Invalid option, please select a valid number."
            fi
        done
    fi
    echo "Nvidia's proprietary drivers provide superior performance and official support on Nvidia hardware."
    read -rp "Do you want Nvidia proprietary drivers? [y/N]: " use_nvidia
    if [[ "${use_nvidia}" == [Yy]* ]]; then
        image_name+="-nvidia"
        echo "Nvidia's proprietary drivers with open source kernel modules are recommended for Turing or newer cards (GTX 16XX+)."
        read -rp "Do you want Nvidia's proprietary drivers with open source kernel modules? [Y/n]: " use_open
        use_open=${use_open:-y}
        [[ "${use_open}" == [Yy]* ]] && image_name+="-open"
    else
        image_name+="-main"
    fi
    image_name+="-hardened"
    if [[ -f "/usr/bin/rpm-ostree" ]]; then
        full_ref=$(crane digest --full-ref "ghcr.io/secureblue/${image_name}:latest")
        rebase_command="rpm-ostree rebase ostree-image-signed:docker://ghcr.io/secureblue/${image_name}:latest"
    else
        full_ref=$(crane digest --full-ref "ghcr.io/secureblue/${image_name}:uki")
        rebase_command="run0 -i bootc switch ghcr.io/secureblue/${image_name}:uki"
    fi
    slsa-verifier verify-image --source-uri "github.com/secureblue/secureblue" --source-branch "live" "${full_ref}"
    printf "Command to execute:\n%s\n\n" "${rebase_command}"
    read -rp "Proceed? [y/N]: " rebase_proceed
    if [[ "${rebase_proceed}" == [Yy]* ]]; then
        eval "${rebase_command}"
    fi

# Apply SELinux type "user_home_t" on external drives to allow access from Trivalent
label-external-drives:
    #!/usr/bin/bash
    set -euo pipefail
    media_paths=("/run/media/${USER}/" "/mnt/")
    selabel="user_home_t"
    supported_fs=("ext2" "ext3" "ext4" "jfs" "xfs" "btrfs") # ref: https://wiki.gentoo.org/wiki/SELinux/FAQ#Can_I_use_SELinux_with_any_file_system.3F

    echo "Warning: This will label your drives mounted on paths $(printf '"%s" and ' "${media_paths[@]}" | sed 's/ and $//') such that they are treated as an extension to your home directory. (You can select which ones to label)"
    echo 'If you do not want Trivalent to have access to these drives, do not proceed.'
    read -rp 'Are you sure you want to do this? [y/N] ' warning_proceed
    if ! [[ "${warning_proceed}" == [Yy]* ]]; then
        echo 'Aborting.'
        exit 0
    fi

    for media_path in "${media_paths[@]}"; do
        if [[ -z "$( ls -A "${media_path}" 2>&- )" ]]; then
            echo
            echo "You don't have any drives mounted in \"${media_path}\", skipping..."
            continue
        fi

        for dir in "${media_path}"*/
        do
            echo
            if [[ "$(stat -c '%U' "${dir}")" != "${USER}" ]]; then
                echo "Drive root folder is not owned by you, skipping drive \"${dir}\"..."
                continue
            fi
            detected_fs="$(df -T "${dir}" | awk '{print $2}' | sed -n 2p)"
            if ! printf "%s\n" "${supported_fs[@]}" | grep -Fxq "${detected_fs}"; then
                echo "SELinux support is unknown for filesystem ${detected_fs}, skipping drive \"${dir}\"..."
                continue
            fi
            read -rp "Do you want to label \"${dir}\"? [y/N] " proceed
            if ! [[ "${proceed}" == [Yy]* ]]; then
                echo 'Skipping...'
                continue
            fi
            echo "Labeling drive mounted on \"${dir}\" with ${selabel}"
            dir=${dir%*/} # remove trailing slash
            if ! run0 sh -c 'semanage fcontext -a -t "$1" "$2(/.*)?" && restorecon -r "$2"' sh "${selabel}" "${dir}"; then
                echo 'Execution failed, aborting.'
                exit 1
            fi
        done
    done

    echo -e '\nDone.'

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
        usermod -aG usbguard "${SUDO_USER}"
        usbguard generate-policy > /etc/usbguard/rules.conf
        sed -i "/^IPCAllowedGroups=wheel/s/\$/ usbguard/" /etc/usbguard/usbguard-daemon.conf
        restorecon -vR /var/log/usbguard
        systemctl enable --now usbguard.service
        usbguard add-user "${SUDO_USER}"
    '
    if ! grep -Eq '^IMAGE_ID=.*(securecore|iot)' /usr/lib/os-release; then
        systemctl enable --user --now usbguard-notifier.service
    fi
