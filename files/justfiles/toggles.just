# Toggle the cups service on/off
toggle-cups:
    #! /bin/run0 /bin/bash
    if systemctl is-enabled --quiet cups; then
      firewall-cmd --permanent --remove-port=631/tcp
      firewall-cmd --permanent --remove-port=631/udp
      firewall-cmd --reload
      systemctl mask cups
      systemctl disable cups
      systemctl stop cups
      systemctl daemon-reload
      echo "Cups disabled."
    else
      firewall-cmd --permanent --add-port=631/tcp
      firewall-cmd --permanent --add-port=631/udp
      firewall-cmd --reload
      systemctl unmask cups
      systemctl enable cups
      systemctl start cups
      systemctl daemon-reload
      echo "Cups enabled."
    fi

# Toggle bluetooth kernel modules on/off (requires reboot)
toggle-bluetooth-modules:
    #! /bin/run0 /bin/bash
    BLUE_MOD_FILE="/etc/modprobe.d/99-bluetooth.conf"
    if test -e $BLUE_MOD_FILE; then
      rm -f $BLUE_MOD_FILE
      echo "Bluetooth kernel modules disabled. Reboot to take effect."
    else
      sh -c 'echo "install bluetooth /sbin/modprobe --ignore-install bluetooth" >> "$1"' _ "$BLUE_MOD_FILE"
      sh -c 'echo "install btusb /sbin/modprobe --ignore-install btusb" >> "$1"' _ "$BLUE_MOD_FILE"
      chmod 644 $BLUE_MOD_FILE
      echo "Bluetooth kernel modules enabled. Reboot to take effect."
    fi

# Toggle GHNS (KDE Get New Stuff)
toggle-ghns:
    #! /bin/run0 /bin/bash
    KDE_GLOBALS_FILE="/etc/xdg/kdeglobals"
    if test -e $KDE_GLOBALS_FILE; then
      if grep -q "ghns=false" "$KDE_GLOBALS_FILE"; then
        sed -i "s/ghns=false/ghns=true/" "$KDE_GLOBALS_FILE"
        echo "GHNS enabled."
      elif grep -q "ghns=true" "$KDE_GLOBALS_FILE"; then
        sed -i "s/ghns=true/ghns=false/" "$KDE_GLOBALS_FILE"
        echo "GHNS disabled."
      else
        echo "The kdeglobals file is missing the ghns toggle."
      fi
    else
      echo "No kdeglobals file found. Are you on kinoite?"
    fi

# enable a kernel module that is disabled by modprobe.d (requires restart)
override-enable-module mod_name:
    #! /bin/run0 /bin/bash
    MOD_NAME="{{ mod_name }}"
    MOD_FILE="/etc/modprobe.d/99-$MOD_NAME.conf"
    if test -e $MOD_FILE; then
      echo "$MOD_NAME module is already enabled."
    else
      sh -c 'echo "install $1 /sbin/modprobe --ignore-install $1" >> "$2"' _ "$MOD_NAME" "$MOD_FILE"
      chmod 644 $MOD_FILE
      echo "Override created to enable $MOD_NAME module. Reboot to take effect."
    fi

# reset the override by `just override-enable-module`, i.e. disable the module again (requires restart)
override-reset-module mod_name:
    #! /bin/run0 /bin/bash
    MOD_NAME="{{ mod_name }}"
    MOD_FILE="/etc/modprobe.d/99-$MOD_NAME.conf"
    if test -e $MOD_FILE; then
      rm -f $MOD_FILE
      echo "The override for $MOD_NAME module has been reset. Reboot to take effect."
    else
      echo "No override found for $MOD_NAME module."
    fi

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
    if grep -q "kernel.yama.ptrace_scope = 3" "$SYSCTL_HARDENING_FILE"; then
        sed -i "s/kernel.yama.ptrace_scope = 3/kernel.yama.ptrace_scope = 1/" "$SYSCTL_HARDENING_FILE"
        echo "Anticheat support enabled. ptrace_scope set to 1."
    elif grep -q "kernel.yama.ptrace_scope = 1" "$SYSCTL_HARDENING_FILE"; then
        sed -i "s/kernel.yama.ptrace_scope = 1/kernel.yama.ptrace_scope = 3/" "$SYSCTL_HARDENING_FILE"
        echo "Anticheat support disabled. ptrace_scope set back to 3."
    else
        echo "The sysctl hardening file is missing the ptrace_scope setting."
    fi

# Toggle Gnome JIT JavaScript for GJS and WebkitGTK (requires session restart)
toggle-gnome-jit-js:
    #! /bin/run0 /bin/bash
    ENV_FILE="/etc/profile.d/gnome-disable-jit.sh"
    if test -e $ENV_FILE; then
        rm -f $ENV_FILE
        echo "JIT JavaScript for Gnome and WebkitGTK has been enabled."
    else
        cp /usr$ENV_FILE $ENV_FILE
        chmod 644 $ENV_FILE
        echo "JIT JavaScript for Gnome and WebkitGTK has been disabled."
    fi

# Toggle support for using GNOME user extensions
toggle-gnome-extensions:
    #!/usr/bin/bash
    GSETTING="$(gsettings get org.gnome.shell allow-extension-installation)"
    if [[ "${GSETTING}" == "false" ]]; then
      gsettings set org.gnome.shell allow-extension-installation true
      echo "Support for GNOME user extensions have been enabled"
    else
      gsettings reset org.gnome.shell allow-extension-installation
      echo "Support for GNOME user extensions have been disabled"
    fi

# Toggle Xwayland support
toggle-xwayland ACTION="prompt":
    #! /bin/run0 /bin/bash
    source /usr/lib/ujust/ujust.sh
    OPTION={{ ACTION }}
    if [ "$OPTION" == "prompt" ]; then
      IMAGE="$(rpm-ostree status | grep '●')"
      if [ -n "$(echo $IMAGE | grep 'silverblue')" ] ; then
          OPTION=gnome
      elif [ -n "$(echo $IMAGE | grep 'kinoite')" ] ; then
          OPTION=plasma
      elif [ -n "$(echo $IMAGE | grep 'sericea')" ] || [ -n "$(echo $IMAGE | grep 'sway')" ] ; then
          OPTION=sway
      else
        echo "${bold}Toggling Xwayland (requires logout)${normal}"
        echo 'For which DE/WM do you want to toggle Xwayland?'
        OPTION=$(ugum choose "GNOME" "KDE Plasma" "Sway")
      fi
    elif [ "$OPTION" == "help" ]; then
      echo "Usage: ujust toggle-xwayland <option>"
      echo "  <option>: Specify the quick option - 'gnome', 'plasma', or 'sway'"
      echo "  Use 'gnome' to Toggle Xwayland for GNOME."
      echo "  Use 'plasma' to Toggle Xwayland for KDE Plasma."
      echo "  Use 'sway' to Toggle Xwayland for Sway."
      exit 0
    fi
    if [ "${OPTION,,}" == "gnome" ]; then
      GNOME_XWAYLAND_FILE="/etc/systemd/user/org.gnome.Shell@wayland.service.d/override.conf"
      if test -e $GNOME_XWAYLAND_FILE; then
        rm -f $GNOME_XWAYLAND_FILE
        echo "Xwayland for GNOME has been enabled."
      else
        cp /usr$GNOME_XWAYLAND_FILE $GNOME_XWAYLAND_FILE
        chmod 644 $GNOME_XWAYLAND_FILE
        echo "Xwayland for GNOME has been disabled."
      fi
    elif [ "$OPTION" == "KDE Plasma" ] || [ "${OPTION,,}" == "plasma" ]; then
      PLASMA_XWAYLAND_FILE="/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf"
      if test -e $PLASMA_XWAYLAND_FILE; then
        rm -f $PLASMA_XWAYLAND_FILE
        echo "Xwayland for KDE Plasma has been enabled."
      else
        cp /usr$PLASMA_XWAYLAND_FILE $PLASMA_XWAYLAND_FILE
        chmod 644 $PLASMA_XWAYLAND_FILE
        echo "Xwayland for KDE Plasma has been disabled."
      fi
    elif [ "${OPTION,,}" == "sway" ]; then
      SWAY_XWAYLAND_FILE="/etc/sway/config.d/99-noxwayland.conf"
      if test -e $SWAY_XWAYLAND_FILE; then
        rm -f $SWAY_XWAYLAND_FILE
        echo "Xwayland for Sway has been enabled."
      else
        cp /usr$SWAY_XWAYLAND_FILE $SWAY_XWAYLAND_FILE
        chmod 644 $SWAY_XWAYLAND_FILE
        echo "Xwayland for Sway has been disabled."
      fi
    fi

# Toggle bash environment lockdown (mitigates LD_PRELOAD attacks)
toggle-bash-environment-lockdown:
    #!/usr/bin/bash
    BASH_ENV_FILES=("$HOME/.bashrc" "$HOME/.bash_profile")
    echo "${b}WARNING${n} This will overwrite your .bashrc and .bash_profile."
    echo "This is needed to ensure the mitigation is effective."
    echo "Do you understand?"
    echo "Please type in \"YES I UNDERSTAND\" and press enter"
    read ACCEPT
    if [ "$ACCEPT" == "YES I UNDERSTAND" ]; then
      if lsattr "${BASH_ENV_FILES[0]}" 2>/dev/null | awk '{print $1}' | grep -q 'i'; then
        echo "Bash environment '(${BASH_ENV_FILES[@]})' is locked down. Unlocking it."
        for file in "${BASH_ENV_FILES[@]}"; do
            run0 chattr -i "$file"
        done
      else
        echo "Bash environment '(${BASH_ENV_FILES[@]})' is unlocked. Locking it."
        echo "
    # .bashrc

    # Source global definitions
    if [ -f /etc/bashrc ]; then
        . /etc/bashrc
    fi

    # User specific environment
    if ! [[ "\$PATH" =~ "\$HOME/.local/bin:\$HOME/bin:" ]]; then
        PATH="\$HOME/.local/bin:\$HOME/bin:\$PATH"
    fi
    export PATH

    # Uncomment the following line if you don't like systemctl's auto-paging feature:
    # export SYSTEMD_PAGER=

    unset rc
          " > ~/.bashrc

        echo "
    # .bash_profile

    # Get the aliases and functions
    if [ -f ~/.bashrc ]; then
        . ~/.bashrc
    fi

    # User specific environment and startup programs
        " > ~/.bash_profile

        for file in "${BASH_ENV_FILES[@]}"; do
            run0 chattr +i "$file"
        done
      fi
    else
      echo "Capitalization matters when you type \"YES I UNDERSTAND\""
    fi

# Toggle unconfined domain userns creation
toggle-unconfined-domain-userns-creation:
    #! /bin/run0 /bin/bash
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
    MODULE_NAME="harden_container_userns"

    if semodule -l | grep -q "$MODULE_NAME"; then
        echo "Module $MODULE_NAME is currently enabled. Disabling the hardening, enabling container domain userns (e.g. for distrobox)."
        semodule --disable="$MODULE_NAME"
        echo "Module $MODULE_NAME disabled. Container domain userns enabled."
    else
        echo "Module $MODULE_NAME is not currently enabled. Enabling the hardening, disabling container domain userns (e.g. for distrobox)."
        semodule --enable="$MODULE_NAME"
        echo "Module $MODULE_NAME enabled. Container domain userns disabled."
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
        read -p "Do you want to use per-connection Wi-Fi MAC address randomization? [y/N]" randomization_level
        randomization_level=${randomization_level:-n}

        if [ "$randomization_level" == [Yy]* ]; then
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
        echo "MAC randomization enabled."
        systemctl restart NetworkManager
    fi
