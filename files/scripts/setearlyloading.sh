#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i 's@omit_drivers@force_drivers@g' /usr/lib/dracut/dracut.conf.d/99-nvidia.conf
sed -i 's@nvidia-uvm@nvidia-uvm i915 amdgpu@g' /usr/lib/dracut/dracut.conf.d/99-nvidia-dracut.conf


if [ ! -f /usr/libexec/rpm-ostree/wrapped/dracut ]; then
    rpm-ostree cliwrap install-to-root /
fi

QUALIFIED_KERNEL="$(rpm -qa | grep -P 'kernel-(|'"$KERNEL_SUFFIX"'-)(\d+\.\d+\.\d+)' | sed -E 's/kernel-(|'"$KERNEL_SUFFIX"'-)//')"

/usr/libexec/rpm-ostree/wrapped/dracut --no-hostonly --kver "$QUALIFIED_KERNEL" --reproducible -v --add ostree -f "/lib/modules/$QUALIFIED_KERNEL/initramfs.img"

chmod 0600 "/lib/modules/$QUALIFIED_KERNEL/initramfs.img"