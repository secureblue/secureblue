import '100-bling.just'
# Include some of your custom scripts here!

# Add additional boot parameters for hardening (requires reboot)
set-kargs-hardening:
    rpm-ostree kargs --append="init_on_alloc=1" --append="init_on_free=1" --append="slab_nomerge" --append="page_alloc.shuffle=1" --append="randomize_kstack_offset=on" --append="vsyscall=none" --append="debugfs=off" --append="lockdown=confidentiality" --append="random.trust_cpu=off" --append="random.trust_bootloader=off" --append="intel_iommu=on" --append="amd_iommu=on" --append="iommu.passthrough=0" --append="iommu.strict=1" --append="pti=on" --append="mitigations=auto,nosmt"

set-kargs-hardening-unstable:
    echo "Warning: setting these kargs may lead to boot issues on some hardware."
    rpm-ostree kargs --append="efi=disable_early_pci_dma" --append="module.sig_enforce=1" 

harden-flatpak:
    flatpak override --user --filesystem=host-os:ro --env=LD_PRELOAD=/var/run/host/usr/lib64/libhardened_malloc.so

enable-cups:
    firewall-cmd --permanent --add-port=631/tcp
    firewall-cmd --permanent --add-port=631/udp 
    firewall-cmd --reload 
    systemctl unmask cups
    systemctl enable cups
    systemctl start cups
