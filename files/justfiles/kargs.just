# Add additional boot parameters for hardening (requires reboot)
set-kargs-hardening:
    #!/usr/bin/bash
    read -p "Do you need support for 32-bit processes/syscalls? (This is mostly used by legacy software, with some exceptions, such as Steam) [y/N]: " YES
    if [[ "$YES" == [Yy]* ]]; then
        echo "Keeping 32-bit support."
    else
        IAEMU_NO="--append-if-missing=ia32_emulation=0"
        echo "Disabling 32-bit support, for the next boot."
    fi
    read -p "Do you want to force disable Simultaneous Multithreading (SMT) / Hyperthreading? (This can cause a reduction in the performance of certain tasks in favor of security) (Note that in most hardware SMT will be disabled anyways to mitigate a known vulnerability, this turns it off on all hardware regardless) [y/N]: " YES
    if [[ "$YES" == [Yy]* ]]; then
        NOSMT_YES="--append-if-missing=nosmt=force"
        echo "Force disabling SMT/Hyperthreading."
    else
        echo "Not force disabling SMT/Hyperthreading."
    fi
    read -p "Would you like to set additional (unstable) hardening kargs? (Warning: Setting these kargs may lead to boot or stability issues on some hardware.) [y/N]: " YES
    if [[ "$YES" == [Yy]* ]]; then
    UNSTABLE_YES="--append-if-missing=efi=disable_early_pci_dma \
        --append-if-missing=gather_data_sampling=force \
        --append-if-missing=amd_iommu=force_isolation \
        --append-if-missing=debugfs=off"
        echo "Setting unstable hardening kargs."
    else
        echo "Not setting unstable hardening kargs."
    fi
    echo "Applying boot parameters..."
    rpm-ostree kargs \
      ${UNSTABLE_YES:+$UNSTABLE_YES} ${IAEMU_NO:+$IAEMU_NO} ${NOSMT_YES:+$NOSMT_YES} \
      --append-if-missing=init_on_alloc=1 \
      --append-if-missing=init_on_free=1 \
      --append-if-missing=slab_nomerge \
      --append-if-missing=page_alloc.shuffle=1 \
      --append-if-missing=randomize_kstack_offset=on \
      --append-if-missing=vsyscall=none \
      --append-if-missing=lockdown=confidentiality \
      --append-if-missing=random.trust_cpu=off \
      --append-if-missing=random.trust_bootloader=off \
      --append-if-missing=iommu=force \
      --append-if-missing=intel_iommu=on \
      --append-if-missing=iommu.passthrough=0 \
      --append-if-missing=iommu.strict=1 \
      --append-if-missing=pti=on \
      --append-if-missing=module.sig_enforce=1 \
      --append-if-missing=mitigations=auto,nosmt \
      --append-if-missing=spectre_v2=on \
      --append-if-missing=spec_store_bypass_disable=on \
      --append-if-missing=l1d_flush=on \
      --append-if-missing=l1tf=full,force \
      --append-if-missing=kvm-intel.vmentry_l1d_flush=always
    echo "Hardening kargs applied."

# Remove all hardening boot parameters (requires reboot)
remove-kargs-hardening:
    #!/usr/bin/bash
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
      --delete-if-present="gather_data_sampling=force" \
      --delete-if-present="ia32_emulation=0" \
      --delete-if-present="l1tf=full,force" \
      --delete-if-present="kvm-intel.vmentry_l1d_flush=always" \
      --delete-if-present="nosmt=force"
    echo "Hardening kargs removed."

# Set nvidia kargs
set-kargs-nvidia:
    #!/usr/bin/bash
    rpm-ostree kargs \
      --append-if-missing=rd.driver.blacklist=nouveau \
      --append-if-missing=modprobe.blacklist=nouveau \
      --append-if-missing=nvidia-drm.modeset=1 \
      --append-if-missing=nvidia-drm.fbdev=1
