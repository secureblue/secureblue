# Add additional boot parameters for hardening (requires reboot)
set-kargs-hardening:
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

set-kargs-hardening-unstable:
    echo "Warning: setting these kargs may lead to boot issues on some hardware."
    rpm-ostree kargs \
      --append-if-missing="efi=disable_early_pci_dma" \
      --append-if-missing="debugfs=off"

harden-flatpak:
    flatpak override --user --filesystem=host-os:ro --env=LD_PRELOAD=/var/run/host/usr/lib64/libhardened_malloc.so

enable-cups:
    firewall-cmd --permanent --add-port=631/tcp
    firewall-cmd --permanent --add-port=631/udp 
    firewall-cmd --reload 
    systemctl unmask cups
    systemctl enable cups
    systemctl start cups
