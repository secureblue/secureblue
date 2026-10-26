# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# enable a kernel module that is disabled by modprobe.d (requires restart)
override-enable-module mod_name:
    #! /bin/run0 /bin/bash
    MOD_NAME="{{ mod_name }}"
    MOD_FILE="/etc/modprobe.d/99-${MOD_NAME}.conf"
    if [[ -e "${MOD_FILE}" ]]; then
        echo "${MOD_NAME} module is already enabled."
    else
        sh -c 'echo "install $1 /sbin/modprobe --ignore-install $1" >> "$2"' _ "${MOD_NAME}" "${MOD_FILE}"
        chmod 644 "${MOD_FILE}"
        echo "Override created to enable ${MOD_NAME} module. Reboot to take effect."
    fi

# reset the override by `just override-enable-module`, i.e. disable the module again (requires restart)
override-reset-module mod_name:
    #! /bin/run0 /bin/bash
    MOD_NAME="{{ mod_name }}"
    MOD_FILE="/etc/modprobe.d/99-${MOD_NAME}.conf"
    if [[ -e "${MOD_FILE}" ]]; then
        rm -f "${MOD_FILE}"
        echo "The override for ${MOD_NAME} module has been reset. Reboot to take effect."
    else
        echo "No override found for ${MOD_NAME} module."
    fi

# Toggle debug mode (requires restart)
toggle-debug-mode:
    #! /bin/run0 /bin/bash
    if test -e /etc/sysctl.d/99-enable-coredump.conf; then
        cp /usr/share/secureblue/etc/security/limits.d/60-disable-coredump.conf /etc/security/limits.d/60-disable-coredump.conf
        cp /usr/share/secureblue/etc/systemd/system.conf.d/60-disable-coredump.conf /etc/systemd/system.conf.d/60-disable-coredump.conf
        cp /usr/share/secureblue/etc/systemd/user.conf.d/60-disable-coredump.conf /etc/systemd/user.conf.d/60-disable-coredump.conf
        rm /etc/sysctl.d/99-enable-coredump.conf
        echo "Debug mode disabled."
    else
        rm /etc/security/limits.d/60-disable-coredump.conf
        rm /etc/systemd/system.conf.d/60-disable-coredump.conf
        rm /etc/systemd/user.conf.d/60-disable-coredump.conf
        echo "kernel.core_pattern = |/usr/lib/systemd/systemd-coredump %P %u %g %s %t %c %h" >/etc/sysctl.d/99-enable-coredump.conf
        echo "Debug mode enabled."
        if [[ "$(getsebool deny_ptrace)" == *'--> on' ]]; then
            setsebool deny_ptrace off
            echo "Temporarily enabled ptrace for this session."
        fi
    fi

# Toggle bash environment lockdown (mitigates LD_PRELOAD attacks). Use skip_approval to bypass initial prompt.
toggle-bash-environment-lockdown skip_approval="false":
    #!/bin/bash
    set -euo pipefail
    # shellcheck disable=SC1091
    source /usr/lib/ujust/libformatting.sh

    user_home=~
    if [[ ! -d "${user_home}" ]]; then
        echo "User homedir not found."
        exit 1
    fi

    if lsattr "${user_home}/.bashrc" 2>/dev/null | awk '{print $1}' | grep -q 'i'; then
        pending_status="unlocked"
    else
        pending_status="locked"
    fi

    # Below variable is created to only call date once and use the same time across the script despite execution time.
    current_time="$(date | tr ' ' '_')"

    if [[ "${pending_status}" == "locked" ]]; then
        # shellcheck disable=SC2154
        echo "${bold}WARNING${unbold} This will change your ~/.bashrc, ~/.bash_profile, ~/.config/bash_completion, ~/.profile, ~/.bash_logout, ~/.bash_login, ~/.bashrc.d/, and ~/.config/environment.d/"
        echo "This is needed to ensure the mitigation (see LD_PRELOAD attacks) is effective."
        echo "This script will create backups of the old versions in ~/bash_env_files/${current_time}."
    else
        echo "${bold}WARNING${unbold} .bashrc, .bash_profile, and more will be unlocked and made editable by non-root users. This represents a security risk (see LD_PRELOAD attacks)"
    fi

    # shellcheck disable=SC2050
    if [[ "{{ skip_approval }}" == "false" ]]; then
        echo "Do you understand?"
        accept=""
        read -r -p "Type ${bold}YES I UNDERSTAND${unbold} and press ${bold}Enter${unbold} to continue: " accept
        if [[ "${accept}" != "YES I UNDERSTAND" ]]; then
            exit
        fi
    elif [[ "{{ skip_approval }}" != "true" ]]; then
        echo 'Invalid skip_approval argument, only "true", "false", or empty allowed.'
        exit
    fi

    BASH_ENV_FILES=(
        "${user_home}/.bashrc"
        "${user_home}/.bash_profile"
        "${user_home}/.profile"
        "${user_home}/.bash_logout"
        "${user_home}/.bash_login"
        "${user_home}/.config/bash_completion"
    )

    BASH_ENV_DIRS=(
        "${user_home}/.bashrc.d"
        "${user_home}/.config/environment.d"
    )

    existing_paths=()
    for env_path in "${BASH_ENV_FILES[@]}" "${BASH_ENV_DIRS[@]}"; do
        if [[ -f "${env_path}" || -d "${env_path}" ]]; then
            existing_paths+=("${env_path}")
        fi
    done

    if [[ "${#existing_paths[@]}" -gt 0 ]]; then
        run0 chattr -R -i -- "${existing_paths[@]}"
    fi

    if [[ "${pending_status}" == "locked" ]]; then
        backup_dest="${user_home}/bash_env_files/${current_time}/"
        mkdir -p "${backup_dest}"

        for env_path in "${BASH_ENV_FILES[@]}" "${BASH_ENV_DIRS[@]}"; do
            skel_path="${env_path#"${user_home}/"}"
            backup_file="${backup_dest}${skel_path}"
            if [[ -e "${env_path}" ]]; then
                mkdir -p "$(dirname "${backup_file}")"
                mv "${env_path}" "${backup_file}"
            fi
        done

        install -D -d -m 700 "${BASH_ENV_DIRS[@]}"
        for env_path in "${BASH_ENV_FILES[@]}"; do
            skel_path="${env_path#"${user_home}/"}"
            origin_path="/etc/skel/${skel_path}"
            [[ -f "${origin_path}" ]] || origin_path=/dev/null
            install -D -m 700 "${origin_path}" "${env_path}"
        done

        run0 chattr -R +i -- "${BASH_ENV_FILES[@]}" "${BASH_ENV_DIRS[@]}"
    fi

    echo "${USER}" "${pending_status}."
    echo "${bold}NOTE${unbold}: until a reboot, any process with an open file descriptor will continue to have the access they had before this script was run."

# Toggle MAC Randomization
toggle-mac-randomization:
    #! /bin/run0 /bin/bash
    RAND_MAC_FILE="/etc/NetworkManager/conf.d/rand_mac.conf"

    if test -e "${RAND_MAC_FILE}"; then
        rm -f "${RAND_MAC_FILE}"
        echo "MAC randomization disabled."
        systemctl restart NetworkManager
    else
        echo "MAC randomization can be stable (persisting the same random MAC per access point across disconnects/reboots),"
        echo "or it can be randomized per-connection (every time it connects to the same access point it uses a new MAC)."
        randomization_choice=""
        read -rp "Do you want to use per-connection Wi-Fi MAC address randomization? [y/N] " randomization_choice

        if [[ "${randomization_choice}" == [Yy]* ]]; then
            randomization_level=random
            echo "Selected state: per-connection"
        else
            randomization_level=stable
            echo "Selected state: per-network (stable)"
        fi
        cat <<EOL > "${RAND_MAC_FILE}"
    [device-mac-randomization]
    # "yes" is already the default for scanning
    wifi.scan-rand-mac-address=yes

    [connection-mac-randomization]
    # Generate a random MAC for each Network and associate the two permanently.
    ethernet.cloned-mac-address=stable
    wifi.cloned-mac-address=${randomization_level}
    EOL
        chmod 644 "${RAND_MAC_FILE}"
        echo "MAC randomization enabled."
        systemctl restart NetworkManager
    fi
