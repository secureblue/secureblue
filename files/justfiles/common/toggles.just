# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

# Toggle the cups service on/off
toggle-cups:
    #! /bin/run0 /bin/bash
    if systemctl is-enabled --quiet cups; then
      firewall-cmd --permanent --remove-port=631/tcp
      firewall-cmd --permanent --remove-port=631/udp
      firewall-cmd --reload
      systemctl disable --now cups.socket
      systemctl mask cups.socket
      systemctl disable --now cups.service
      systemctl mask cups.service
      systemctl mask --now avahi-daemon.socket
      systemctl mask --now avahi-daemon.service
      systemctl daemon-reload
      echo "CUPS & avahi-daemon disabled"
    else
      firewall-cmd --permanent --add-port=631/tcp
      firewall-cmd --permanent --add-port=631/udp
      firewall-cmd --reload
      systemctl unmask cups.socket
      systemctl unmask cups.service
      systemctl enable --now cups.socket
      systemctl enable --now cups.service
      systemctl unmask avahi-daemon.service
      systemctl unmask avahi-daemon.socket
      systemctl daemon-reload
      echo "CUPS enabled."
      echo "avahi-daemon is unmasked & will be started as needed on an on-demand basis."
      echo "Note: cups-browsed, the printer discovery service, is still disabled for"
      echo "    security reasons. New network printers will need to be added manually."
      echo "    If you absolutely need network discovery, you can enable the cups-browsed"
      echo "    service at your own risk. Secureblue strongly recommends against this."
    fi

# enable a kernel module that is disabled by modprobe.d (requires restart)
override-enable-module mod_name:
    #! /bin/run0 /bin/bash
    MOD_NAME="{{ mod_name }}"
    MOD_FILE="/etc/modprobe.d/99-$MOD_NAME.conf"
    if [ -e "$MOD_FILE" ]; then
      echo "$MOD_NAME module is already enabled."
    else
      sh -c 'echo "install $1 /sbin/modprobe --ignore-install $1" >> "$2"' _ "$MOD_NAME" "$MOD_FILE"
      chmod 644 "$MOD_FILE"
      echo "Override created to enable $MOD_NAME module. Reboot to take effect."
    fi

# reset the override by `just override-enable-module`, i.e. disable the module again (requires restart)
override-reset-module mod_name:
    #! /bin/run0 /bin/bash
    MOD_NAME="{{ mod_name }}"
    MOD_FILE="/etc/modprobe.d/99-$MOD_NAME.conf"
    if [ -e "$MOD_FILE" ]; then
      rm -f "$MOD_FILE"
      echo "The override for $MOD_NAME module has been reset. Reboot to take effect."
    else
      echo "No override found for $MOD_NAME module."
    fi

# disable the webcam kernel module
disable-webcam:
    #! /bin/run0 /bin/bash
    WEBCAM_MOD_FILE="/etc/modprobe.d/99-disable-webcam.conf"
    if [ -e "$WEBCAM_MOD_FILE" ]; then
      echo "Webcam module is already disabled."
    else
      echo "install uvcvideo /bin/false" > "$WEBCAM_MOD_FILE" 
      chmod 644 "$WEBCAM_MOD_FILE"
      echo "Override created to disable the webcam module. Reboot to take effect."
    fi

# reset the webcam kernel module
reset-webcam:
    #! /bin/run0 /bin/bash
    WEBCAM_MOD_FILE="/etc/modprobe.d/99-disable-webcam.conf"
    rm -f "$WEBCAM_MOD_FILE"
    echo "Webcam module reset."

# Toggle debug mode (requires restart)
toggle-debug-mode:
    #! /bin/run0 /bin/bash
    if test -e /etc/sysctl.d/99-enable-coredump.conf; then
        cp /usr/etc/security/limits.d/60-disable-coredump.conf /etc/security/limits.d/60-disable-coredump.conf
        cp /usr/etc/systemd/system.conf.d/60-disable-coredump.conf /etc/systemd/system.conf.d/60-disable-coredump.conf
        cp /usr/etc/systemd/user.conf.d/60-disable-coredump.conf /etc/systemd/user.conf.d/60-disable-coredump.conf
        rm /etc/sysctl.d/99-enable-coredump.conf
        echo "Debug mode disabled."
    else
        rm /etc/security/limits.d/60-disable-coredump.conf
        rm /etc/systemd/system.conf.d/60-disable-coredump.conf
        rm /etc/systemd/user.conf.d/60-disable-coredump.conf
        echo "kernel.core_pattern = |/usr/lib/systemd/systemd-coredump %P %u %g %s %t %c %h" >/etc/sysctl.d/99-enable-coredump.conf
        echo "Debug mode enabled."
        if [[ $(</proc/sys/kernel/yama/ptrace_scope) != 1 ]]; then
            echo "ptrace is restricted in this session. Some debuggers may not work as intended. Use ujust toggle-ptrace-scope to manage ptrace."
        fi
    fi

alias toggle-ptrace-scope := toggle-anticheat-support

# Toggle anticheat support by changing ptrace scope (requires restart)
toggle-anticheat-support:
    #! /bin/run0 /bin/bash
    SYSCTL_HARDENING_FILE="/etc/sysctl.d/60-hardening.conf"
    if grep -q '^kernel.yama.ptrace_scope = 3' "$SYSCTL_HARDENING_FILE"; then
        sed -i 's/^kernel.yama.ptrace_scope =.*/kernel.yama.ptrace_scope = 1/' "$SYSCTL_HARDENING_FILE"
        echo "Anticheat support enabled. ptrace_scope set to 1. Reboot to take effect."
    elif grep -q 'kernel.yama.ptrace_scope = 1' "$SYSCTL_HARDENING_FILE"; then
        sed -i 's/^kernel.yama.ptrace_scope =.*/kernel.yama.ptrace_scope = 3/' "$SYSCTL_HARDENING_FILE"
        echo "Anticheat support disabled. ptrace_scope set back to 3. Reboot to take effect."
    else
        echo "The sysctl hardening file is missing the ptrace_scope setting."
    fi

# Toggle bash environment lockdown (mitigates LD_PRELOAD attacks). Use skip_approval to bypass initial prompt, and apply_for_all_users to bypass secondary prompt.
toggle-bash-environment-lockdown skip_approval="false" apply_for_all_users="prompt":
    #!/bin/run0 /bin/bash
    set -euo pipefail
    source /usr/lib/ujust/libformatting.sh

    # The below function fetches the minimium and maximium UIDS as configured in /etc/login.defs.
    # Any UIDs within this change are true user ids rather than system agents, and therefore
    # should be locked down. The user_string variable uses this fetched UID range to find all
    # existing users and their home directory along with formatting this data for later use.
    # The IFS line simply converts this data into a bash array.
    function user_list_lookup() {
        uid_min="$(grep -Po '^\s*UID_MIN\s+\K\d+' /etc/login.defs)"
        uid_max="$(grep -Po '^\s*UID_MAX\s+\K\d+' /etc/login.defs)"
        user_string="$(getent passwd | awk -F':' -v max="$uid_max" -v min="$uid_min" 'max >= $3 && $3 >= min {print $1}' | tr '\n' ',' | sed 's/,*$//')"
        IFS=',' read -ra user_list <<< "$user_string"
    }

    # $SUDO_USER is the user who started the script instead of whichever authorized it via polkit
    # or the root home. From there this $USER_HOME uses getent to lookup their home directory to
    # later check if they have an existing .bashrc file.
    user_home="$(getent passwd "$SUDO_USER" | cut -d: -f6)"
    if lsattr "$user_home/.bashrc" 2>/dev/null | awk '{print $1}' | grep -q 'i'; then
        pending_status="unlocked"
    else
        pending_status="locked"
    fi

    # Below variable is created to only call date once and use the same time across the script
    # despite execution time.
    current_time="$(date | tr ' ' '_')"

    if [[ "$pending_status" == "locked" ]]; then
        echo "${bold}WARNING${unbold} This will change your ~/.bashrc, ~/.bash_profile, ~/.config/bash_completion, ~/.profile, ~/.bash_logout, ~/.bash_login, ~/.bashrc.d/, and ~/.config/environment.d/"
        echo "This is needed to ensure the mitigation (see LD_PRELOAD attacks) is effective."
        echo "This script will create backups of the old versions in ~/bash_env_files/$current_time."
    else
        echo "${bold}WARNING${unbold} .bashrc, .bash_profile, and more will be unlocked and made editable by non-root users. This represents a security risk (see LD_PRELOAD attacks)"
    fi

    # shellcheck disable=SC2050
    if [[ "{{ skip_approval }}" == "false" ]]; then
        echo "Do you understand?"
        echo 'Please type in "YES I UNDERSTAND" and press enter'
        read -r accept
        if [[ "$accept" != "YES I UNDERSTAND" ]]; then
            exit
        fi
    elif [[ "{{ skip_approval }}" != "true" ]]; then
        echo 'Invalid skip_approval arguement, only "true", "false", or empty allowed.'
        exit
    fi

    # shellcheck disable=SC2050
    if [[ "{{ apply_for_all_users }}" == "prompt" ]]; then
        user_list_lookup
        echo "Do you want this change to apply to ${bold}all${unbold} users (${user_list[*]})? [y/N]"
        echo "Otherwise, it will only apply to the user who launched this script ($SUDO_USER)."
        read -r reply
        if [[ "$reply" != [yY]* ]]; then
            user_list=("$SUDO_USER")
        fi
    elif [[ "{{ apply_for_all_users }}" == "false" ]]; then
        user_list=("$SUDO_USER")
    elif [[ "{{ apply_for_all_users }}" == "true" ]]; then
        user_list_lookup
    else
        echo 'Invalid apply_for_all_users arguement, only "true", "false", or empty allowed.'
        exit
    fi

    for user in "${user_list[@]}"; do
        echo "Applying for user: $user"
        user_home="$(getent passwd "$user" | awk -F':' '{ print $6}')"
        [ -d "$user_home" ] || { echo "Variable \$user_home for $user is somehow empty (check your getent passwd entries)"; echo "safely exiting."; exit 1; }

        BASH_ENV_FILES=(
            "$user_home/.bashrc"
            "$user_home/.bash_profile"
            "$user_home/.config/bash_completion"
            "$user_home/.profile"
            "$user_home/.bash_logout"
            "$user_home/.bash_login"
            "$user_home/.bashrc.d/"
            "$user_home/.config/environment.d/"
        )

        # Purpose of the below block is to actually lock or unlock the current selected user
        # across the configured BASH_ENV_FILES
        #    If the script is locking:
        #        to copy the old env files and directories to folder with the time appended to its name
        #        remove immutability (to allow the script to overwrite any existing immutable environment files)
        #        create default or blank copies (deleting the old versions)
        #        add immutability

        if [[ "$pending_status" == "locked" ]]; then
            backup_dest="$user_home/bash_env_files/$current_time/"
            mkdir -p "$backup_dest"

            for file in "${BASH_ENV_FILES[@]}"; do
                # skel_file converts "$user_home/.bashrc" to ".bashrc"
                skel_file="${file#"${user_home}/"}"
                if [ ! -f "$file" ] && [ ! -d "$file" ] && [ -e "$file" ]; then
                    echo "Special file detected on absolute filepath ($file) from BASH_ENV_FILES. It will not be modified."
                elif [ -f "$file" ]; then
                    chattr -i "$file"
                    rsync -a --mkpath "$file" "$backup_dest$skel_file"
                    rm "$file"
                elif [ -d "$file" ]; then
                    chattr -R -i "$file"
                    rsync -a --mkpath "$file" "$backup_dest$skel_file"
                    rm -r "$file"
                fi

                # Now we create new empty/default files and directories
                if [ "${file: -1}" == "/" ]; then
                    install -D -d -o "$user" -g "$user" -m 700 "$file"
                    chattr +i -R "$file"
                elif [ -f "/etc/skel/$skel_file" ]; then
                    install -D -o "$user" -g "$user" -m 700 "/etc/skel/$skel_file" "$file"
                    chattr +i "$file"
                else
                    install -D -o "$user" -g "$user" -m 700 /dev/null "$file"
                    chattr +i "$file"
                fi
            done

            chmod -R 700 "$user_home/bash_env_files"
            chown -R "$user:" "$user_home/bash_env_files"
        else
            for file in "${BASH_ENV_FILES[@]}"; do
                if [ ! -f "$file" ] && [ ! -d "$file" ] && [ -e "$file" ]; then
                    echo "Special file detected on absolute filepath ($file) from BASH_ENV_FILES. It will not be modified."
                elif [ -f "$file" ]; then
                    chattr -i "$file"
                elif [ -d "$file" ]; then
                    chattr -R -i "$file"
                fi
            done
        fi
    done

    echo "${user_list[@]}" "$pending_status."
    echo "${bold}NOTE${unbold}: until a reboot, any process with an open file descriptor will continue to have the access they had before this script was run."

# Toggle unconfined domain userns creation
toggle-unconfined-domain-userns-creation:
    #! /bin/run0 /bin/bash
    set -euo pipefail
    MODULE_NAME="harden_userns"

    if semodule -l | grep -q "$MODULE_NAME"; then
        echo "Module $MODULE_NAME is currently enabled. Disabling the hardening, enabling unconfined domain userns (e.g. for bubblejail)."
        semodule --disable="$MODULE_NAME"
        echo "Module $MODULE_NAME disabled. Unconfined domain userns enabled."
    else
        echo "Module $MODULE_NAME is not currently enabled. Enabling the hardening, disabling unconfined domain userns (e.g. for bubblejail)."
        semodule --enable="$MODULE_NAME"
        echo "Module $MODULE_NAME enabled. Unconfined domain userns disabled."
    fi

# Toggle container domain userns creation
toggle-container-domain-userns-creation:
    #! /bin/run0 /bin/bash
    set -euo pipefail
    MODULE_NAME="harden_container_userns"

    if semodule -l | grep -q "$MODULE_NAME"; then
        echo "Module $MODULE_NAME is currently enabled. Disabling the hardening, enabling container domain userns (e.g. for distrobox)."
        semodule --disable="$MODULE_NAME"
        echo "Module $MODULE_NAME disabled. Container domain userns enabled."
    else
        echo "Module $MODULE_NAME is not currently enabled. Enabling the hardening, disabling container domain userns (e.g. for distrobox)."

        echo 'Warning: This will stop ALL containers and shut down podman.'
        read -rp 'Are you sure you want to do this? (y/N) ' proceed
        if ! [[ "$proceed" == [Yy]* ]]; then
            echo "Aborting..."
            exit 0
        fi

        semodule --enable="$MODULE_NAME"
        echo "Module $MODULE_NAME enabled. Container domain userns disabled."

        echo 'Stopping all containers and shutting down podman...'
        run0 --user="$SUDO_USER" podman stop --all > /dev/null
        killall -u "$SUDO_USER" catatonit || true
        echo 'podman has been shut down.'

        if pgrep -u root -a -x catatonit &> /dev/null; then
            echo 'WARNING: Catatonit running as root detected, reboot your machine to reset podman state.'
        fi
    fi

# Toggle MAC Randomization
toggle-mac-randomization:
    #! /bin/run0 /bin/bash
    RAND_MAC_FILE="/etc/NetworkManager/conf.d/rand_mac.conf"

    if test -e $RAND_MAC_FILE; then
        rm -f $RAND_MAC_FILE
        echo "MAC randomization disabled."
        systemctl restart NetworkManager
    else
        echo "MAC randomization can be stable (persisting the same random MAC per access point across disconnects/reboots),"
        echo "or it can be randomized per-connection (every time it connects to the same access point it uses a new MAC)."
        randomization_choice=""
        read -rp "Do you want to use per-connection Wi-Fi MAC address randomization? [y/N] " randomization_choice

        if [[ "$randomization_choice" == [Yy]* ]]; then
            randomization_level=random
            echo "Selected state: per-connection"
        else
            randomization_level=stable
            echo "Selected state: per-network (stable)"
        fi
        cat <<EOL > $RAND_MAC_FILE
    [device-mac-randomization]
    # "yes" is already the default for scanning
    wifi.scan-rand-mac-address=yes

    [connection-mac-randomization]
    # Generate a random MAC for each Network and associate the two permanently.
    ethernet.cloned-mac-address=stable
    wifi.cloned-mac-address=$randomization_level
    EOL
        chmod 644 $RAND_MAC_FILE
        echo "MAC randomization enabled."
        systemctl restart NetworkManager
    fi
