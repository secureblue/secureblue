# Secureblue Post Install Recommendations

After rebasing to secureblue, the following steps are recommended.

## Nvidia
If you are using an nvidia image, run this after installation:

```
rpm-ostree kargs \
    --append-if-missing=rd.driver.blacklist=nouveau \
    --append-if-missing=modprobe.blacklist=nouveau \
    --append-if-missing=nvidia-drm.modeset=1
```

### Nvidia optimus laptop
If you are using an nvidia image on an optimus laptop, run this after installation:

```
ujust configure-nvidia-optimus
```

## Enroll secureboot key

```ujust enroll-secure-boot-key```

## Set kargs

Documentation is available [here](https://github.com/secureblue/secureblue/blob/live/files/system/usr/share/ublue-os/just/60-custom.just.readme.md) for the kargs set by the commands below.

### Set hardened kargs

```ujust set-kargs-hardening```

### Set unstable hardened kargs

*Can cause issues on some hardware, but stable on other hardware* [[1]](https://github.com/secureblue/secureblue/issues/169) [[2]](https://github.com/secureblue/secureblue/issues/215)

```ujust set-kargs-hardening-unstable```

## Setup USBGuard

*This will generate a policy based on your currently attached USB devices and block all others, then enable usbguard*

```ujust setup-usbguard```

## GRUB
### Set a password

Setting a GRUB password helps protect the device from physical tampering and mitigates various attack vectors, such as booting from malicious media devices and changing boot or kernel parameters.

By default, the password will be required when modifying boot entries, but not when booting existing entries.

To set a GRUB password, use the following command.

```sudo grub2-setpassword```

GRUB will prompt for a username and password. The default username is root.

If you wish to password-protect booting existing entries, you can add the `grub_users root` entry in the specific configuration file located in the `/boot/loader/entries` directory.

## User setup
### Create a separate wheel account for admin purposes

Creating a dedicated wheel user and removing wheel from your primary user helps prevent certain attack vectors, like:

- https://www.kicksecure.com/wiki/Dev/Strong_Linux_User_Account_Isolation#LD_PRELOAD
- https://www.kicksecure.com/wiki/Root#Prevent_Malware_from_Sniffing_the_Root_Password

> [!CAUTION]
> If you do these steps out of order, it is possible to end up without the ability to administrate your system. You will not be able to use the [traditional GRUB-based method](https://linuxconfig.org/recover-reset-forgotten-linux-root-password) of fixing mistakes like this, either, as this will leave your system in a broken state. However, simply rolling back to an older snapshot of your system, should resolve the problem.

1. ```adduser admin```
2. ```usermod -aG wheel admin```
3. ```passwd admin```
4. ```reboot```

> [!NOTE]
> We log in as admin to do the final step of removing the user account's wheel privileges in order to make the operation of removing those privileges depend on having access to your admin account, and the admin account functioning correctly first.

5. Log in as `admin`
6. ```gpasswd -d {your username here} wheel```
7. ```reboot```

### Avoid `wheel` by using dedicated groups
When not in the wheel group, a user can be added to a dedicated group, otherwise certain actions are blocked:

- use virtual machines with a QEMU system session: `libvirt`
- use `adb` and `fastboot`: `plugdev`

To create a custom new group with associated polkit rules, use the guide in the FAQ

### Add a SELinux confined user
[SELinux confined users](https://fedoraproject.org/wiki/SELinux/ConfinedUsers) are a project to secure not only the core system, but also the user accounts with [SELinux](https://docs.fedoraproject.org/en-US/quick-docs/selinux-getting-started/).

At the current state, unlike on Android, a user account and all it's processes are not protected by SELinux on Fedora.

SELinux confined users have different access levels. From most privileged to least privileged:
- `sysadm_u`
- `staff_u`
- `user_u`

Example for adding a user with the loose `sysadm_u` protection

```
sudo useradd sysadm-confined
sudo passwd sysadm-confined
sudo usermod -aG wheel sysadm-confined
sudo semanage login -a -s sysadm_u sysadm-confined
```

## Chromium extension

1. Go to [uBlock Origin Lite](https://chromewebstore.google.com/detail/ublock-origin-lite/ddkjiahejlhfcafbddmgiahcphecmpfh?pli=1) ([Why Lite?](https://developer.chrome.com/docs/extensions/develop/migrate/improve-security))
2. Install it
3. In the extension's settings, make sure all of the lists under Default and Miscellaneous are checked (and at your preference, lists in the Annoyances section or country-specific lists)


## Instruction set optimizations for hardened_malloc

Please see the description for release [v2.2.0](https://github.com/secureblue/secureblue/releases/tag/v2.2.0)
