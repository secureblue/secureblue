## Included in set-kargs-hardening

**Zero newly allocated pages and heaps, mitigating use-after-free vulnerabilities**

`init_on_alloc=1` 

**Fills freed pages and heaps with zeroes, mitigating use-after-free vulnerabilities**

`init_on_free=1` 

**Disables the merging of slabs, increasing difficulty of heap exploitation**

`slab_nomerge`

**Enables page allocator freelist randomization, reducing page allocation predictability**

`page_alloc.shuffle=1` 

**Randomize kernel stack offset on each syscall, making certain types of attacks more difficult**

`randomize_kstack_offset=on` 

**Disable vsyscall as it is both obsolete and enables an ROP attack vector**

`vsyscall=none` 

**Enable kernel lockdown in the strictest mode**

`lockdown=confidentiality` 

**Disable CPU-based entropy sources as it's not auditable and has resulted in vulnerabilities**

`random.trust_cpu=off` 

**Disable trusting the use of the a seed passed by the bootloader**

`random.trust_bootloader=off`

**Mitigate DMA attacks by enabling IOMMU**

`iommu=force` 
`intel_iommu=on` 
`amd_iommu=force_isolation` 

**Disable IOMMU bypass**

`iommu.passthrough=0` 

**Synchronously invalidate IOMMU hardware TLBs**

`iommu.strict=1` 

**Enable kernel page table isolation**

`pti=on` 

**Only allows kernel modules that have been signed with a valid key to be loaded**

`module.sig_enforce=1` 

**Automatically mitigate all known CPU vulnerabilities, including disabling SMT if necessary.**

`mitigations=auto,nosmt` 

**Turn on spectre_v2 mitigations at boot time for all programs**

`spectre_v2=on` 

**Disable spec store bypass for all programs**

`spec_store_bypass_disable=on`

**Enable the mechanism to flush the L1D cache on context switch.**

`l1d_flush=on`

**Mitigate unprivileged speculative access to data by using the microcode mitigation when available or by disabling AVX on affected systems where the microcode hasn’t been updated to include the mitigation.**

`gather_data_sampling=force`

## Included in set-kargs-hardening-unstable

**Fill IOMMU protection gap by setting the busmaster bit during early boot**

`efi=disable_early_pci_dma`

**Disable debugfs to prevent exposure of sensitive kernel information**

`debugfs=off` 
