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
    #!/usr/bin/pkexec /usr/bin/bash
    echo "Notice: This will generate a policy based on your existing connected USB devices."
    sudo mkdir -p /var/log/usbguard
    sudo mkdir -p /etc/usbguard
    sudo chmod 755 /etc/usbguard
    sudo sh -c 'usbguard generate-policy > /etc/usbguard/rules.conf'
    sudo systemctl enable --now usbguard.service
    sudo usbguard add-user $(whoami)
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

