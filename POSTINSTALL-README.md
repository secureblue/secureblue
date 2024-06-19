# secureblue

After rebasing to secureblue, the following steps are recommended.

## Enroll secureboot key

```ujust enroll-secure-boot-key```

## Set kargs

Documentation is available [here](https://github.com/secureblue/secureblue/blob/live/config/files/usr/share/ublue-os/just/60-custom.just.readme.md) for the kargs set by the commands below.

### Set hardened kargs

```ujust set-kargs-hardening```

### Set unstable hardened kargs

*Can cause issues on some hardware, but stable on other hardware*

```ujust set-kargs-hardening-unstable```


## GRUB
### Set a password

Setting a GRUB password helps protect the device from physical tampering and mitigates various attack vectors, such as booting from malicious media devices and changing boot or kernel parameters.

To set a GRUB password, use the following command. By default, the password will be required when modifying boot entries, but not when booting existing entries.

```sudo grub2-setpassword```

GRUB will prompt for a username and password. The default username is root.

If you wish to password-protect booting existing entries, you can add the `grub_users root` entry in the specific configuration file located in the `/boot/loader/entries` directory.

## Create a separate wheel account for admin purposes

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

When not in the wheel group, a user can be added to a dedicated group, otherwise certain actions are blocked:

- use virtual machines: `libvirt`
- use `adb` and `fastboot`: `plugdev`
- use systemwide flatpaks: `flatpak`

Some actions don't have an associated group yet, you can create your own rules and groups to fix this.

**Example**: To allow a non-wheel user to use LUKS encrypted external drives:

1. `sudo groupadd diskadmin`
2. `sudo usermod -aG diskadmin {your username here}`
3. execute this command (*explanation below*)

```
cat >> /etc/polkit-1/rules.d/80-udisks2.rules <<EOF
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.udisks2.encrypted-unlock-system" || action.id == "org.freedesktop.udisks2.filesystem-mount-system" &&
        subject.active == true && subject.local == true &&
        subject.isInGroup("diskadmin"))
        {
        return polkit.Result.YES;
    }
});
EOF
```

The custom rule allows the group`diskadmin` to do the actions for unlocking and mounting these drives. Note the requirement on `active` and `local`, and the exactly specified actions.

## Chromium extension

1. Go to [uBlock Origin Lite](https://chromewebstore.google.com/detail/ublock-origin-lite/ddkjiahejlhfcafbddmgiahcphecmpfh?pli=1) ([Why Lite?](https://developer.chrome.com/docs/extensions/develop/migrate/improve-security))
2. Install it
3. In the extension's settings, make sure all of the lists under Default and Miscellaneous are checked (and at your preference, lists in the Annoyances section or country-specific lists)


## Instruction set optimizations for hardened_malloc

Please see the description for release [v2.2.0](https://github.com/secureblue/secureblue/releases/tag/v2.2.0)
