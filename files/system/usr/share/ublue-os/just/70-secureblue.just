# Add additional boot parameters for hardening (requires reboot)
set-kargs-hardening:
    #!/usr/bin/pkexec /usr/bin/bash
    rpm-ostree kargs \
      --append-if-missing="init_on_alloc=1" \
      --append-if-missing="init_on_free=1" \
      --append-if-missing="slab_nomerge" \
      --append-if-missing="page_alloc.shuffle=1" \
      --append-if-missing="randomize_kstack_offset=on" \
      --append-if-missing="vsyscall=none" \
      --append-if-missing="lockdown=confidentiality" \
      --append-if-missing="random.trust_cpu=off" \
      --append-if-missing="random.trust_bootloader=off" \
      --append-if-missing="iommu=force" \
      --append-if-missing="intel_iommu=on" \
      --append-if-missing="amd_iommu=force_isolation" \
      --append-if-missing="iommu.passthrough=0" \
      --append-if-missing="iommu.strict=1" \
      --append-if-missing="pti=on" \
      --append-if-missing="module.sig_enforce=1" \
      --append-if-missing="mitigations=auto,nosmt" \
      --append-if-missing="spectre_v2=on" \
      --append-if-missing="spec_store_bypass_disable=on" \
      --append-if-missing="l1d_flush=on" \
      --append-if-missing="gather_data_sampling=force"
    echo "Hardening kargs set."

# Add additional (unstable) boot parameters for hardening (requires reboot)
set-kargs-hardening-unstable:
    #!/usr/bin/pkexec /usr/bin/bash
    echo "Warning: setting these kargs may lead to boot issues on some hardware."
    rpm-ostree kargs \
      --append-if-missing="efi=disable_early_pci_dma" \
      --append-if-missing="debugfs=off"

    echo "Unstable hardening kargs set."

# Remove all hardening boot parameters (requires reboot)
remove-kargs-hardening:
    #!/usr/bin/pkexec /usr/bin/bash
    rpm-ostree kargs \
      --delete-if-present="init_on_alloc=1" \
      --delete-if-present="init_on_free=1" \
      --delete-if-present="slab_nomerge" \
      --delete-if-present="page_alloc.shuffle=1" \
      --delete-if-present="randomize_kstack_offset=on" \
      --delete-if-present="vsyscall=none" \
      --delete-if-present="lockdown=confidentiality" \
      --delete-if-present="random.trust_cpu=off" \
      --delete-if-present="random.trust_bootloader=off" \
      --delete-if-present="iommu=force" \
      --delete-if-present="intel_iommu=on" \
      --delete-if-present="amd_iommu=force_isolation" \
      --delete-if-present="iommu.passthrough=0" \
      --delete-if-present="iommu.strict=1" \
      --delete-if-present="pti=on" \
      --delete-if-present="module.sig_enforce=1" \
      --delete-if-present="mitigations=auto,nosmt" \
      --delete-if-present="efi=disable_early_pci_dma" \
      --delete-if-present="debugfs=off" \
      --delete-if-present="spectre_v2=on" \
      --delete-if-present="spec_store_bypass_disable=on" \
      --delete-if-present="l1d_flush=on" \
      --delete-if-present="gather_data_sampling=force"
    echo "Hardening kargs removed."

# Harden flatpaks by preloading hardened_malloc (highest supported hwcap)
harden-flatpak:
    #!/usr/bin/bash
    flatpak override --user --filesystem=host-os:ro
    uarches="$(/usr/lib64/ld-linux-x86-64.so.2 --help | grep '(supported, searched)' | cut -d'v' -f2)"
    bestuarch="${uarches:0:1}"
    if [ -z "$bestuarch" ] ; then
        echo "No microarchitecture support detected. Using default x86-64-v1 architecture."
        flatpak override --user --env=LD_PRELOAD=/var/run/host/usr/lib64/libhardened_malloc.so
    else
        echo "x86-64-v$bestuarch support detected. Using x86-64-v$bestuarch microarchitecture."
        flatpak override --user --env=LD_PRELOAD=/var/run/host/usr/lib64/glibc-hwcaps/x86-64-v"$bestuarch"/libhardened_malloc.so
    fi

# Toggle the cups service on/off
toggle-cups:
    #!/usr/bin/pkexec /usr/bin/bash
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
    #!/usr/bin/pkexec /usr/bin/bash
    BLUE_MOD_FILE="/etc/modprobe.d/99-bluetooth.conf"
    if test -e $BLUE_MOD_FILE; then
      sudo rm -f $BLUE_MOD_FILE
      echo "Bluetooth kernel modules disabled. Reboot to take effect."
    else
      sudo sh -c 'echo "install bluetooth /sbin/modprobe --ignore-install bluetooth" >> "$1"' _ "$BLUE_MOD_FILE"
      sudo sh -c 'echo "install btusb /sbin/modprobe --ignore-install btusb" >> "$1"' _ "$BLUE_MOD_FILE"
      sudo chmod 644 $BLUE_MOD_FILE
      echo "Bluetooth kernel modules enabled. Reboot to take effect."
    fi

# Toggle GHNS (KDE Get New Stuff)
toggle-ghns:
    #!/usr/bin/pkexec /usr/bin/bash
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
    #!/usr/bin/pkexec /usr/bin/bash
    MOD_NAME="{{ mod_name }}"
    MOD_FILE="/etc/modprobe.d/99-$MOD_NAME.conf"
    if test -e $MOD_FILE; then
      echo "$MOD_NAME module is already enabled."
    else
      sudo sh -c 'echo "install $1 /sbin/modprobe --ignore-install $1" >> "$2"' _ "$MOD_NAME" "$MOD_FILE" 
      sudo chmod 644 $MOD_FILE
      echo "Override created to enable $MOD_NAME module. Reboot to take effect."
    fi
  
# reset the override by `just override-enable-module`, i.e. disable the module again (requires restart)
override-reset-module mod_name:
    #!/usr/bin/pkexec /usr/bin/bash
    MOD_NAME="{{ mod_name }}"
    MOD_FILE="/etc/modprobe.d/99-$MOD_NAME.conf"
    if test -e $MOD_FILE; then
      sudo rm -f $MOD_FILE
      echo "The override for $MOD_NAME module has been reset. Reboot to take effect."
    else
      echo "No override found for $MOD_NAME module."
    fi


# Setup USBGuard
setup-usbguard:
    #!/usr/bin/bash
    echo "Notice: This will generate a policy based on your existing connected USB devices."
    ACTIVE_USERNAME=$(whoami)
    pkexec sh -c '
        mkdir -p /var/log/usbguard
        mkdir -p /etc/usbguard
        chmod 755 /etc/usbguard
        usbguard generate-policy > /etc/usbguard/rules.conf
        systemctl enable --now usbguard.service
        usbguard add-user $1
    ' -- $ACTIVE_USERNAME
    systemctl enable --user --now usbguard-notifier.service

# Rerun Yafti
rerun-yafti:
    yafti -f /usr/share/ublue-os/firstboot/yafti.yml


# Toggle anticheat support by changing ptrace scope (requires restart)
toggle-anticheat-support:
    #!/usr/bin/pkexec /usr/bin/bash
    SYSCTL_HARDENING_FILE="/etc/sysctl.d/hardening.conf"
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
    #!/usr/bin/pkexec /usr/bin/bash
    ENV_FILE="/etc/profile.d/gnome-disable-jit.sh"
    if test -e $ENV_FILE; then
        sudo rm -f $ENV_FILE
        echo "JIT JavaScript for Gnome and WebkitGTK has been enabled."
    else
        sudo cp /usr$ENV_FILE $ENV_FILE
        sudo chmod 644 $ENV_FILE
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
    #!/usr/bin/pkexec /usr/bin/bash
    source /usr/lib/ujust/ujust.sh
    OPTION={{ ACTION }}
    if [ "$OPTION" == "prompt" ]; then
      echo "${bold}Toggling Xwayland (requires logout)${normal}"
      echo 'For which DE/WM do you want to toggle Xwayland?'
      OPTION=$(ugum choose "GNOME" "KDE Plasma" "Sway")
    elif [ "$OPTION" == "help" ]; then
      echo "Usage: ujust toggle-xwayland <option>"
      echo "  <option>: Specify the quick option - 'gnome', 'plasma', or 'sway'"
      echo "  Use 'gnome' to Toggle Xwayland for GNOME."
      echo "  Use 'plasma' to Toggle Xwayland for KDE Plasma."
      echo "  Use 'sway' to Toggle Xwayland for Sway."
      exit 0
    fi
    if [ "$OPTION" == "GNOME" ] || [ "${OPTION,,}" == "gnome" ]; then
      GNOME_XWAYLAND_FILE="/etc/systemd/user/org.gnome.Shell@wayland.service.d/override.conf"
      if test -e $GNOME_XWAYLAND_FILE; then
        sudo rm -f $GNOME_XWAYLAND_FILE
        echo "Xwayland for GNOME has been enabled."
      else
        sudo cp /usr$GNOME_XWAYLAND_FILE $GNOME_XWAYLAND_FILE
        sudo chmod 644 $GNOME_XWAYLAND_FILE
        echo "Xwayland for GNOME has been disabled."
      fi
    elif [ "$OPTION" == "KDE Plasma" ] || [ "${OPTION,,}" == "plasma" ]; then
      PLASMA_XWAYLAND_FILE="/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf"
      if test -e $PLASMA_XWAYLAND_FILE; then
        sudo rm -f $PLASMA_XWAYLAND_FILE
        echo "Xwayland for KDE Plasma has been enabled."
      else
        sudo cp /usr$PLASMA_XWAYLAND_FILE $PLASMA_XWAYLAND_FILE
        sudo chmod 644 $PLASMA_XWAYLAND_FILE
        echo "Xwayland for KDE Plasma has been disabled."
      fi
    elif [ "$OPTION" == "Sway" ] || [ "${OPTION,,}" == "sway" ]; then
      SWAY_XWAYLAND_FILE="/etc/sway/config.d/99-noxwayland.conf"
      if test -e $SWAY_XWAYLAND_FILE; then
        sudo rm -f $SWAY_XWAYLAND_FILE
        echo "Xwayland for Sway has been enabled."
      else
        sudo cp /usr$SWAY_XWAYLAND_FILE $SWAY_XWAYLAND_FILE
        sudo chmod 644 $SWAY_XWAYLAND_FILE
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
            pkexec chattr -i "$file"
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
            pkexec chattr +i "$file"
        done
      fi
    else
      echo "Capitalization matters when you type \"YES I UNDERSTAND\""
    fi

# Audit secureblue
audit-secureblue:
    #!/bin/bash

    STATUS_SUCCESS="SUCCESS"
    STATUS_WARNING="WARNING"
    STATUS_FAILURE="FAILURE"
    print_status() {
        local check_name="$1"
        local status="$2"

        local color_code
        case "$status" in
            $STATUS_SUCCESS) color_code=32 ;; # Green
            $STATUS_WARNING) color_code=33 ;; # Yellow
            $STATUS_FAILURE) color_code=31 ;;    # Red
            *) color_code=0 ;;
        esac

        local formatted_status
        formatted_status=$(printf "%*s" $(( (7 + ${#status}) / 2 )) "$status")
        formatted_status=$(printf "%-7s" "$formatted_status")

        printf "%-64s [ \033[%dm%s\033[0m ]\n" "$check_name"... "$color_code" "$formatted_status"
    }

    hasPermission() {
        local permissions=$1
        local prefix=$2
        local query=$3
        local line=$(grep "^${prefix}=" <<< "$permissions" | sed -e "s/^${prefix}=//" -e "s/#.*//")
        IFS=';' read -r -a list <<< "$line"
        for p in ${list[@]}; do
            if [[ "$p" =~ ^$query$ ]]; then
                return
            fi
        done
        return 1
    }

    KARGS=$(rpm-ostree kargs)
    KARGS_LIST=(
        "init_on_alloc=1"
        "init_on_free=1"
        "slab_nomerge"
        "page_alloc.shuffle=1"
        "randomize_kstack_offset=on"
        "vsyscall=none"
        "lockdown=confidentiality"
        "random.trust_cpu=off"
        "random.trust_bootloader=off"
        "iommu=force"
        "intel_iommu=on"
        "amd_iommu=force_isolation"
        "iommu.passthrough=0"
        "iommu.strict=1"
        "pti=on"
        "module.sig_enforce=1"
        "mitigations=auto,nosmt"
        "spectre_v2=on"
        "spec_store_bypass_disable=on"
        "l1d_flush=on"
        "gather_data_sampling=force"
        "efi=disable_early_pci_dma"
        "debugfs=off"
    )

    for karg in "${KARGS_LIST[@]}"; do
        KARG_TEST_STRING="Checking for $karg karg"
        if echo "$KARGS" | grep -q "$karg"; then
            print_status "$KARG_TEST_STRING" "$STATUS_SUCCESS"
        else
            print_status "$KARG_TEST_STRING" "$STATUS_FAILURE"
        fi
    done

    SYSCTL_TEST_STRING="Ensuring no sysctl overrides"
    if diff /usr/etc/sysctl.d/hardening.conf /etc/sysctl.d/hardening.conf > /dev/null; then
        print_status "$SYSCTL_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$SYSCTL_TEST_STRING" "$STATUS_FAILURE"
    fi

    SYSCTL_TEST_STRING="Ensuring no modprobe overrides"
    if diff /usr/etc/modprobe.d/blacklist.conf /etc/modprobe.d/blacklist.conf > /dev/null; then
        print_status "$SYSCTL_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$SYSCTL_TEST_STRING" "$STATUS_FAILURE"
    fi

    AUTHSELECT_TEST_STRING="Ensuring no authselect overrides"
    if diff /usr/etc/authselect /etc/authselect --suppress-common-lines -r > /dev/null; then
        print_status "$AUTHSELECT_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$AUTHSELECT_TEST_STRING" "$STATUS_FAILURE"
    fi


    USBGUARD_TEST_STRING="Ensuring usbguard is active"
    if systemctl is-active --quiet usbguard; then
        print_status "$USBGUARD_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$USBGUARD_TEST_STRING" "$STATUS_FAILURE"
    fi


    CHRONYD_TEST_STRING="Ensuring chronyd is active"
    if systemctl is-active --quiet chronyd; then
        print_status "$CHRONYD_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$CHRONYD_TEST_STRING" "$STATUS_FAILURE"
    fi

    BASH_TEST_STRING="Ensuring bash environment lockdown"
    BASH_ENV_FILES=(~/.bashrc ~/.bash_profile)
    all_locked=1

    for file in "${BASH_ENV_FILES[@]}"; do
        if [ -f "$file" ]; then
            if lsattr "$file" 2>/dev/null | awk '{print $1}' | grep -q 'i'; then
                continue
            else
                all_locked=0
                break
            fi
        else
            all_locked=0
            break
        fi
    done

    if [ "$all_locked" -eq 1 ]; then
        print_status "$BASH_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$BASH_TEST_STRING" "$STATUS_FAILURE"
    fi

    WHEEL_TEST_STRING="Ensuring user is not a member of wheel"
    if groups | grep -q "\bwheel\b"; then
        print_status "$WHEEL_TEST_STRING" "$STATUS_FAILURE"
    else
        print_status "$WHEEL_TEST_STRING" "$STATUS_SUCCESS"
    fi

    GNOME_XWAYLAND_TEST_STRING="Ensuring xwayland is disabled for GNOME"
    if [ -f "/etc/systemd/user/org.gnome.Shell@wayland.service.d/override.conf" ]; then
        print_status "$GNOME_XWAYLAND_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$GNOME_XWAYLAND_TEST_STRING" "$STATUS_FAILURE"
    fi

    PLASMA_XWAYLAND_TEST_STRING="Ensuring xwayland is disabled for KDE Plasma"
    if [ -f "/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf" ]; then
        print_status "$PLASMA_XWAYLAND_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$PLASMA_XWAYLAND_TEST_STRING" "$STATUS_FAILURE"
    fi

    SWAY_XWAYLAND_TEST_STRING="Ensuring xwayland is disabled for Sway"
    if [ -f "/etc/sway/config.d/99-noxwayland.conf" ]; then
        print_status "$SWAY_XWAYLAND_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$SWAY_XWAYLAND_TEST_STRING" "$STATUS_FAILURE"
    fi

    EXTENSIONS_TEST_STRING="Ensuring GNOME user extensions are disabled"
    if command -v gnome-shell &> /dev/null; then
        if [ "$(gsettings get org.gnome.shell allow-extension-installation)" = "false" ]; then
            print_status "$EXTENSIONS_TEST_STRING" "$STATUS_SUCCESS"
        else
            print_status "$EXTENSIONS_TEST_STRING" "$STATUS_FAILURE"
        fi
    fi

    SELINUX_TEST_STRING="Ensuring SELinux is in Enforcing mode"
    if [ "$(getenforce)" = "Enforcing" ]; then
        print_status "$SELINUX_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$SELINUX_TEST_STRING" "$STATUS_FAILURE"
    fi

    ENVIRONMENT_TEST_STRING="Ensuring no environment file overrides"
    if diff /usr/etc/environment /etc/environment > /dev/null; then
        print_status "$ENVIRONMENT_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$ENVIRONMENT_TEST_STRING" "$STATUS_WARNING"
    fi

    GHNS_TEST_STRING="Ensuring KDE GHNS is disabled"
    KDE_GLOBALS_FILE="/etc/xdg/kdeglobals"
    if test -e $KDE_GLOBALS_FILE; then
        GHNS_STRING="$(grep 'ghns=false' $KDE_GLOBALS_FILE)"
        if [[ $GHNS_STRING == "ghns=false" ]]; then
            print_status "$GHNS_TEST_STRING" "$STATUS_SUCCESS"
        else
            print_status "$GHNS_TEST_STRING" "$STATUS_FAILURE"
        fi
    fi

    HARDENED_MALLOC_TEST_STRING="Ensuring hardened_malloc is set in ld.so.preload"
    if diff /usr/etc/ld.so.preload /etc/ld.so.preload > /dev/null; then
        print_status "$HARDENED_MALLOC_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$HARDENED_MALLOC_TEST_STRING" "$STATUS_FAILURE"
    fi

    SECUREBOOT_TEST_STRING="Ensuring secure boot is enabled"
    if [ "$(mokutil --sb-state)" == "SecureBoot enabled" ]; then
        print_status "$SECUREBOOT_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$SECUREBOOT_TEST_STRING" "$STATUS_FAILURE"
    fi

    if command -v flatpak &> /dev/null; then
        remotes="$(flatpak remotes -d)"
        while read -r remote ; do
            ref="$(cut -f 1 <<<"$remote")"
            url="$(cut -f 3 <<< "$remote")"
            subset="$(cut -f 5 <<< "$remote")"
            remote_string="Auditing flatpak remote $ref"
            if [[ "$url" != "https://dl.flathub.org/repo/" && "$url" != "https://dl.flathub.org/beta-repo/" ]]; then
                print_status "$remote_string" "$STATUS_FAILURE"
                echo "> $ref is configured with an unknown url!"
            elif [ "$subset" != "verified" ]; then
                print_status "$remote_string" "$STATUS_FAILURE"
                echo "> $ref is not a verified repo!"
            else
                print_status "$remote_string" "$STATUS_SUCCESS"
            fi
        done <<< "$remotes"
        
        declare -A flatpaks
        while read -r ref version; do
            flatpaks+=(["${ref}"]="${ref}//${version}")
        done <<<$(flatpak list | sort -k 1 | cut --fields 2,4)
        for f in ${!flatpaks[@]}; do
            warnings=()
            status="$STATUS_SUCCESS"
            fullref=${flatpaks["$f"]}
            permissions=$(flatpak info --show-permissions "$fullref")

            if hasPermission "$permissions" "shared" "network"; then
                [[ "$status" != "$STATUS_FAILURE" ]] && status="$STATUS_WARNING"
                warnings+=("> $f has network access!")
            fi
            if hasPermission "$permissions" "sockets" "x11" && ! hasPermission "$permissions" "sockets" "fallback-x11"; then
                status="$STATUS_FAILURE"
                warnings+=("> $f has x11 access!")
            fi
            if ! hasPermission "$permissions" "LD_PRELOAD" .*"/libhardened_malloc.so"; then
                status="$STATUS_FAILURE"
                warnings+=("> $f is not using hardened_malloc!")
            fi
            flatpak_test_string="Auditing $f"
            print_status "$flatpak_test_string" "$status"
            for warning in "${warnings[@]}"; do
                echo "$warning"
            done
        done
    fi

