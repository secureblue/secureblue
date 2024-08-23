#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# Reference: https://gist.github.com/ok-ryoko/1ff42a805d496cb1ca22e5cdf6ddefb0#usrbinchage

whitelist=(
    # Needed for flatpak on no-userns images
    "/usr/bin/bwrap"
    # Requires cap_setuid if the suid bit is removed
    "/usr/bin/gpasswd"
    # "In effect, when the SUID bit is unset on /usr/bin/mount, mount(8) will never drop permissions. If /usr/bin/mount were to have a"
    # "nonempty permitted capability set and its effective capability bit were set, then mount(8) would never have its effective " 
    # "capability set cleared during execution, potentially allowing unprivileged users to perform actions they shouldn’t be able to perform"
    # https://gist.github.com/ok-ryoko/1ff42a805d496cb1ca22e5cdf6ddefb0#can-we-replace-the-suid-bit-with-zero-or-more-file-capabilities-4
    "/usr/bin/mount"
    # Required for nvidia images
    "/usr/bin/nvidia-modprobe"
    # https://gist.github.com/ok-ryoko/1ff42a805d496cb1ca22e5cdf6ddefb0#can-we-replace-the-suid-bit-with-zero-or-more-file-capabilities
    "/usr/bin/passwd"
    # https://gist.github.com/ok-ryoko/1ff42a805d496cb1ca22e5cdf6ddefb0#why-does-this-binary-need-to-be-suid-root-9
    "/usr/bin/pkexec"
    # https://gist.github.com/ok-ryoko/1ff42a805d496cb1ca22e5cdf6ddefb0#can-we-replace-the-suid-bit-with-zero-or-more-file-capabilities-6
    "/usr/bin/su"
    # https://gist.github.com/ok-ryoko/1ff42a805d496cb1ca22e5cdf6ddefb0#can-we-replace-the-suid-bit-with-zero-or-more-file-capabilities-6
    "/usr/bin/sudo"
    # See /usr/bin/mount
    "/usr/bin/umount"
    # https://gitlab.freedesktop.org/polkit/polkit/-/issues/168
    "/usr/lib/polkit-1/polkit-agent-helper-1"
    # https://github.com/secureblue/secureblue/issues/119
    "/usr/lib64/libhardened_malloc-light.so"
    "/usr/lib64/libhardened_malloc-pkey.so"
    "/usr/lib64/libhardened_malloc.so"
    # Required for chrome suid sandbox on no-userns images
    "/usr/lib64/chromium-browser/chrome-sandbox"
    # https://github.com/secureblue/secureblue/issues/119
    "/usr/lib64/glibc-hwcaps/x86-64/libhardened_malloc-light.so"
    "/usr/lib64/glibc-hwcaps/x86-64/libhardened_malloc-pkey.so"
    "/usr/lib64/glibc-hwcaps/x86-64/libhardened_malloc.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v2/libhardened_malloc-light.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v2/libhardened_malloc-pkey.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v2/libhardened_malloc.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v3/libhardened_malloc-light.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v3/libhardened_malloc-pkey.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v3/libhardened_malloc.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v4/libhardened_malloc-light.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v4/libhardened_malloc-pkey.so"
    "/usr/lib64/glibc-hwcaps/x86-64-v4/libhardened_malloc.so"
    # Requires cap_setgid,cap_setuid if the SUID bit is removed
    "/usr/sbin/grub2-set-bootflag"
)


is_in_whitelist() {
    local binary="$1"
    for allowed_binary in "${whitelist[@]}"; do
        if [ "$binary" = "$allowed_binary" ]; then
            return 0
        fi
    done
    return 1
}

find /usr -type f -perm /4000 |
    while IFS= read -r binary; do
        if ! is_in_whitelist "$binary"; then
            echo "Removing SUID bit from $binary"
            chmod u-s "$binary"
            echo "Removed SUID bit from $binary"
        fi
    done

find /usr -type f -perm /2000 |
    while IFS= read -r binary; do
        if ! is_in_whitelist "$binary"; then
            echo "Removing SGID bit from $binary"
            chmod g-s "$binary"
            echo "Removed SGID bit from $binary"
        fi
    done

systemctl enable setcapsforunsuidbinaries.service
