!include /usr/share/ublue-os/just/100-bling.just

# Include some of your custom scripts here!

# Add additional boot parameters for hardening (requires reboot)
set-kargs-hardening:
  rpm-ostree kargs --append="init_on_alloc=1" --append="init_on_free=1" --append="slab_nomerge" --append="page_alloc.shuffle=1" --append="randomize_kstack_offset=on" --append="vsyscall=none" --append="debugfs=off" --append="lockdown=confidentiality" --append="random.trust_cpu=off" --append="random.trust_bootloader=off" --append="intel_iommu=on" --append="amd_iommu=on" --append="efi=disable_early_pci_dma" --append="iommu.passthrough=0" --append="iommu.strict=1" --append="nvme_core.default_ps_max_latency_us=0" --append="mitigations=auto,nosmt"
