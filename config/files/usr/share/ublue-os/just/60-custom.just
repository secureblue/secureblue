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
      --append-if-missing="mitigations=auto,nosmt"
    echo "Hardening kargs set."

# Add additional (unstable) boot parameters for hardening (requires reboot)
set-kargs-hardening-unstable:
    #!/usr/bin/pkexec /usr/bin/bash
    echo "Warning: setting these kargs may lead to boot issues on some hardware."
    rpm-ostree kargs \
      --append-if-missing="efi=disable_early_pci_dma"
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
      --delete-if-present="efi=disable_early_pci_dma"
    echo "Hardening kargs removed."

# Harden flatpaks by preloading hardened_malloc
harden-flatpak:
    #!/usr/bin/bash
    flatpak override --user --filesystem=host-os:ro --env=LD_PRELOAD=/var/run/host/usr/lib64/libhardened_malloc.so

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

# enable a kernel module that is disabled by modprobe.d (require restart)
override-enable-module mod_name:
    #!/usr/bin/pkexec /usr/bin/bash
    MOD_NAME="{{ mod_name }}"
    MOD_FILE="/etc/modprobe.d/99-$MOD_NAME.conf"
    if test -e $MOD_FILE; then
      echo "$MOD_NAME module is already enabled. You might forgot to restart for the override to take effect."
    else
      sudo sh -c 'echo "install $1 /sbin/modprobe --ignore-install $1" >> "$2"' _ "$MOD_NAME" "$MOD_FILE" 
      sudo chmod 644 $MOD_FILE
      echo "Override created to enable $MOD_NAME module. Reboot to take effect."
    fi
  
# reset the override by `just override-enable-module`, i.e. disable the module again (require restart)
override-reset-module mod_name:
    #!/usr/bin/pkexec /usr/bin/bash
    MOD_NAME="{{ mod_name }}"
    MOD_FILE="/etc/modprobe.d/99-$MOD_NAME.conf"
    if test -e $MOD_FILE; then
      sudo rm -f $MOD_FILE
      echo "Override for $MOD_NAME module has been reset. Reboot to take effect."
    else
      echo "No override found for $MOD_NAME module."
    fi
