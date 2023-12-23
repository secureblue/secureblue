# Include some of your custom scripts here!

# Add additional boot parameters for hardening (requires reboot)
set-kargs-hardening:
    rpm-ostree kargs --append="init_on_alloc=1" --append="init_on_free=1" --append="slab_nomerge" --append="page_alloc.shuffle=1" --append="randomize_kstack_offset=on" --append="vsyscall=none" --append="debugfs=off" --append="lockdown=confidentiality" --append="random.trust_cpu=off" --append="random.trust_bootloader=off" --append="intel_iommu=on" --append="amd_iommu=on" --append="efi=disable_early_pci_dma" --append="iommu.passthrough=0" --append="iommu.strict=1" --append="nvme_core.default_ps_max_latency_us=0" --append="mitigations=auto,nosmt" &&\
    echo "Hardening kernel arguments applied."

harden-flatpak:
    flatpak override --user --filesystem=host-os:ro --env=LD_PRELOAD=/var/run/host/usr/lib64/libhardened_malloc.so &&\
    echo "Flatpaks are now using harened_halloc."

enable-cups:
    firewall-cmd --add-service=cups --permanent &&\
    firewall-cmd --reload &&\
    systemctl unmask cups &&\
    systemctl enable --now cups &&\
    echo "CUPS enabled."

disable-cups:
    firewall-cmd --remove-service=cups --permanent &&\
    firewall-cmd --reload &&\
    systemctl stop cups &&\
    systemctl disable cups &&\
    systemctl mask cups &&\
    echo "CUPS disabled."

userns-on
    # test if userns are disabled
    if grep -q "kernel.unprivileged_userns_clone = 0" "/usr/etc/sysctl.d/hardening.conf"; then

        # read the container image reference and change the string
        userns_version=$(rpm-ostree status --json | jq -r '.deployments[0]."container-image-reference"' | sed 's/hardened/userns-&/')
        echo "Rebasing to the user namespaces image..."
        rpm-ostree rebase $userns_version
        echo "Reboot for the changes to apply."

    # test if userns are enabled
    elif grep -q "kernel.unprivileged_userns_clone = 1" "/usr/etc/sysctl.d/hardening.conf"; then
        echo "User namespaces are already enabled."

    else
        echo "The check has failed, please report that error."
        rpm-ostree status --json | jq -r '.deployments[0]."container-image-reference"'
        xdg-open "https://github.com/secureblue/secureblue/issues/new"
    fi

userns-off
    # test it userns are disabled
    if grep -q "kernel.unprivileged_userns_clone = 0" "/usr/etc/sysctl.d/hardening.conf"; then
        echo "User namespaces are already disabled."

    # test if userns are enabled
    elif grep -q "kernel.unprivileged_userns_clone = 1" "/usr/etc/sysctl.d/hardening.conf"; then
        nouserns_version=$(rpm-ostree status --json | jq -r '.deployments[0]."container-image-reference"' | sed 's/-userns//')
        echo "Rebasing to the image without user namespaces..."
        rpm-ostree rebase $nouserns_version
        echo "Reboot for the changes to apply."

    else
        echo "The check has failed, please report that error."
        rpm-ostree status --json | jq -r '.deployments[0]."container-image-reference"'
        xdg-open "https://github.com/secureblue/secureblue/issues/new"
    fi

bluetooth-on
    systemctl unmask bluetooth.service &&\
    systemctl enable --now bluetooth.service &&\
    echo "Bluetooth enabled."

bluetooth-off
    systemctl stop bluetooth.service &&\
    systmctl disable bluetooth.service &&\
    systemctl mask bluetooth.service &&\
    echo "Bluetooth disabled."

flathub-all
    flatpak remote-modify --subset=all flathub &&\
    echo "The Flathub Repository now shows all available Apps."

flathub-verified
    flatpak remote-modify --subset=verified flathub &&\
    echo "The Flathub Repository now shows only verified Apps."

generic-hostname
    hostnamectl set-hostname PC &&\
    echo 'Your hostname is now "PC", making you less unique.'
