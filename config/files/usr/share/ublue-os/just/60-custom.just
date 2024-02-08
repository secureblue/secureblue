import '100-bling.just'
# Include some of your custom scripts here!

# hardening Kernel Arguments
harden_kargs := "init_on_alloc=1" + \
               "init_on_free=1" + \
               "slab_nomerge" + \
               "page_alloc.shuffle=1" + \
               "randomize_kstack_offset=on" + \
               "vsyscall=none" + \
               "debugfs=off" + \
               "lockdown=confidentiality "+ \
               "random.trust_cpu=off" + \
               "random.trust_bootloader=off" + \
               "iommu=force" + \
               "intel_iommu=on" + \
               "amd_iommu=force_isolation" + \
               "iommu.passthrough=0" + \
               "iommu.strict=1" + \
               "pti=on" + \
               "module.sig_enforce=1" + \
               "mitigations=auto,nosmt"

# harden karg that might cause boot issue
# See https://github.com/secureblue/secureblue/issues/169
harden_kargs_unstable := "efi=disable_early_pci_dma"

# Add additional boot parameters for hardening (requires reboot)
set-kargs-hardening:
    rpm-ostree kargs --append-if-missing="{{harden_karg}}" 

set-kargs-hardening-unstable:
    echo "Warning: setting these kargs may lead to boot issues on some hardware."
    rpm-ostree kargs --append-if-missing="{{harden_karg_unstable}}"

# delete boot parameters for hardening
delete-kargs-hardening:
    rpm-ostree kargs --delete-if-present="{{harden_karg}} {{harden_karg_unstable}}"

# enable hardenmalloc for flatpak
harden-flatpak:
    flatpak override --user --filesystem=host-os:ro --env=LD_PRELOAD=/var/run/host/usr/lib64/libhardened_malloc.so

# enable cups print system
enable-cups:
    firewall-cmd --permanent --add-port=631/tcp
    firewall-cmd --permanent --add-port=631/udp 
    firewall-cmd --reload 
    systemctl unmask cups
    systemctl enable cups
    systemctl start cups
