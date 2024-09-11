<p align="center">
  <a href="https://github.com/secureblue/secureblue">
    <img src="https://github.com/secureblue/secureblue/assets/129108030/292e0ecc-50b8-4de5-a11a-bfe292489f6c" href="https://github.com/secureblue/secureblue" width=180 />
  </a>
</p>

<h1 align="center">secureblue</h1>


[![secureblue](https://github.com/secureblue/secureblue/actions/workflows/build.yml/badge.svg)](https://github.com/secureblue/secureblue/actions/workflows/build.yml)
[![Discord](https://img.shields.io/discord/1202086019298500629?style=flat&logo=discord&logoColor=white&label=Discord&labelColor=%235F6AE9&color=%2333CB56)](https://discord.com/invite/qMTv5cKfbF)
[![Donate](https://img.shields.io/badge/Donate-blue.svg)](https://github.com/secureblue/secureblue/blob/live/DONATE.md)

This repo uses [BlueBuild](https://blue-build.org/) to generate hardened operating system images, using [uBlue](https://universal-blue.org)'s [Fedora Atomic](https://fedoraproject.org/atomic-desktops/)-based [base images](https://github.com/orgs/ublue-os/packages?repo_name=main) as a starting point. 

# Scope

secureblue applies hardening with the following goals in mind:

- Increase defenses against the exploitation of both known and unknown vulnerabilities.
- Avoid sacrificing usability for most use cases where possible
- Disabling metrics and data collection by default where they exist, so long as this has no security implications (for example, disabling vscode data collection by default on `dx` images)

The following are not in scope:
- Anything that sacrifices security for "privacy". Fedora is already sufficiently private and "privacy" often serves as a euphemism for security theater. This is especially true when at odds with improving security.
- Anything related to "degoogling" chromium. For example, we will not be replacing hardened-chromium with Brave or ungoogled-chromium. Both of them make changes that sacrifice security for "privacy", such as enabling MV2. <sup>[why?](https://developer.chrome.com/docs/extensions/develop/migrate/improve-security)</sup>

# Hardening

- Installing and enabling [hardened_malloc](https://github.com/GrapheneOS/hardened_malloc) globally, including for flatpaks. <sup>[Thanks to rusty-snake's hardened_malloc spec](https://github.com/rusty-snake/fedora-extras)</sup>
- Installing [hardened-chromium](https://github.com/secureblue/hardened-chromium), which is inspired by and incorporates patches from [Vanadium](https://github.com/GrapheneOS/Vanadium). <sup>[Why chromium?](https://grapheneos.org/usage#web-browsing)</sup> <sup>[Why not flatpak chromium?](https://forum.vivaldi.net/post/669805)</sup>
- Setting numerous hardened sysctl values <sup>[details](https://github.com/secureblue/secureblue/blob/live/files/system/etc/sysctl.d/hardening.conf)</sup>
- Disabling coredumps in limits.conf
- Disabling all ports and services for firewalld
- Adds per-network MAC randomization
- Blacklisting numerous unused kernel modules to reduce attack surface <sup>[details](https://github.com/secureblue/secureblue/blob/live/files/system/etc/modprobe.d/blacklist.conf)</sup>
- Enabling only the [flathub-verified](https://flathub.org/apps/collection/verified/1) remote by default
- Sets numerous hardening kernel arguments (Inspired by [Madaidan's Hardening Guide](https://madaidans-insecurities.github.io/guides/linux-hardening.html)) <sup>[details](https://github.com/secureblue/secureblue/blob/live/files/system/usr/share/ublue-os/just/70-secureblue.just.readme.md)</sup>
- Reduce the sudo timeout to 1 minute
- Require wheel user authentication via polkit for `rpm-ostree install` <sup>[why?](https://github.com/rohanssrao/silverblue-privesc)
- Brute force protection by locking user accounts for 24 hours after 50 failed login attempts, hardened password encryption and password quality suggestions
- Installing usbguard and providing `ujust` commands to automatically configure it
- Installing bubblejail for additional sandboxing tooling
- Set opportunistic DNSSEC and DNSOverTLS for systemd-resolved
- Configure chronyd to use Network Time Security (NTS) <sup>[using chrony config from GrapheneOS](https://github.com/GrapheneOS/infrastructure/blob/main/chrony.conf)</sup>
- Disable KDE GHNS by default <sup>[why?](https://blog.davidedmundson.co.uk/blog/kde-store-content/)</sup>
- Disable install & usage of GNOME user extensions by default
- Use HTTPS for all rpm mirrors
- Set all default container policies to `reject`, `signedBy`, or `sigstoreSigned`
- Remove SUID-root from [numerous binaries](https://github.com/secureblue/secureblue/blob/live/files/scripts/removesuid.sh) and replace functionality [using capabilities](https://github.com/secureblue/secureblue/blob/live/files/system/usr/bin/setcapsforunsuidbinaries)
- Disable Xwayland by default (for GNOME, Plasma, and Sway images)
- Mitigation of [LD_PRELOAD attacks](https://github.com/Aishou/wayland-keylogger) via `ujust toggle-bash-environment-lockdown`
- Disable a variety of services by default (including cups, geoclue, passim, and others)
- Removal of the unmaintained and suid-root fuse2 by default
- (Non-userns variants) Disabling unprivileged user namespaces
- (Non-userns variants) Replacing bubblewrap with bubblewrap-suid so flatpak can be used without unprivileged user namespaces

# Rationale

Fedora is one of the few distributions that ships with selinux and associated tooling built-in and enabled by default. This makes it advantageous as a starting point for building a hardened system. However, out of the box it's lacking hardening in numerous other areas. This project's goal is to improve on that significantly.


For more info on uBlue and BlueBuild, check out the [uBlue homepage](https://universal-blue.org/) and the [BlueBuild homepage](https://blue-build.org/).

# Customization

If you want to add your own customizations on top of secureblue, you are advised strongly against forking. Instead, create a repo for your own image by using the [BlueBuild template](https://github.com/blue-build/template), then change your `base-image` to a secureblue image. This will allow you to apply your customizations to secureblue in a concise and maintainable way, without the need to constantly sync with upstream. 

# FAQ

[FAQ](FAQ.md)

# Installation

Have a look at [PREINSTALL-README](PREINSTALL-README.md) before proceeding.

## Rebasing (Recommended)

To rebase a Fedora Atomic installation, choose an $IMAGE_NAME from the [list below](README.md#images-userns), then follow these steps:

*(Important note: the **only** supported tag is `latest`)*

- First rebase to the unsigned image, to get the proper signing keys and policies installed:
  ```
  rpm-ostree rebase ostree-unverified-registry:ghcr.io/secureblue/$IMAGE_NAME:latest
  ```
- Reboot to complete the rebase:
  ```
  systemctl reboot
  ```
- Then rebase to the signed image, like so:
  ```
  rpm-ostree rebase ostree-image-signed:docker://ghcr.io/secureblue/$IMAGE_NAME:latest
  ```
- Reboot again to complete the installation
  ```
  systemctl reboot
  ```

## ISO 

While it's recommended to use a Fedora Atomic iso to install and then rebase that installation to secureblue, you can also generate an iso and install that directly using [this script](generate_secureblue_iso.sh). Please note you should still follow the [post-install steps](README.md#post-install) when installing from a generated iso:

```
./generate_secureblue_iso.sh
```

# Images <sup>[userns?](USERNS.md)</sup>
## Desktop
### Recommended <sup>[why?](RECOMMENDED.md)</sup>
- `silverblue-main-hardened`
- `silverblue-nvidia-hardened`
- `silverblue-main-userns-hardened`
- `silverblue-nvidia-userns-hardened`
### Stable
- `kinoite-main-hardened`
- `kinoite-nvidia-hardened`
- `aurora-main-hardened`
- `aurora-nvidia-hardened`
- `sericea-main-hardened`
- `sericea-nvidia-hardened`
- `kinoite-main-userns-hardened`
- `kinoite-nvidia-userns-hardened`
- `aurora-main-userns-hardened`
- `aurora-nvidia-userns-hardened`
- `aurora-dx-main-userns-hardened`
- `aurora-dx-nvidia-userns-hardened`
- `sericea-main-userns-hardened`
- `sericea-nvidia-userns-hardened`
- `bluefin-main-hardened`
- `bluefin-nvidia-hardened`
- `bluefin-dx-main-userns-hardened`
- `bluefin-dx-nvidia-userns-hardened`
- `bluefin-main-userns-hardened`
- `bluefin-nvidia-userns-hardened`
### Beta
- `wayblue-wayfire-main-hardened`
- `wayblue-wayfire-nvidia-hardened`
- `wayblue-hyprland-main-hardened`
- `wayblue-hyprland-nvidia-hardened`
- `wayblue-river-main-hardened`
- `wayblue-river-nvidia-hardened`
- `wayblue-sway-main-hardened`
- `wayblue-sway-nvidia-hardened`
- `wayblue-wayfire-main-userns-hardened`
- `wayblue-wayfire-nvidia-userns-hardened`
- `wayblue-hyprland-main-userns-hardened`
- `wayblue-hyprland-nvidia-userns-hardened`
- `wayblue-river-main-userns-hardened`
- `wayblue-river-nvidia-userns-hardened`
- `wayblue-sway-main-userns-hardened`
- `wayblue-sway-nvidia-userns-hardened`
### Experimental
- `cinnamon-main-hardened`
- `cinnamon-nvidia-hardened`
- `cinnamon-main-userns-hardened`
- `cinnamon-nvidia-userns-hardened`
- `cosmic-main-hardened`
- `cosmic-nvidia-hardened`
- `cosmic-main-userns-hardened`
- `cosmic-nvidia-userns-hardened`
### Asus <sup>[source](https://github.com/ublue-os/hwe/tree/main/asus)</sup>
- `silverblue-asus-hardened`
- `silverblue-asus-nvidia-hardened`
- `silverblue-asus-userns-hardened`
- `silverblue-asus-nvidia-userns-hardened`
- `aurora-asus-hardened`
- `aurora-asus-nvidia-hardened`
- `kinoite-asus-hardened`
- `kinoite-asus-nvidia-hardened`
- `aurora-asus-userns-hardened`
- `aurora-asus-nvidia-userns-hardened`
- `aurora-dx-asus-userns-hardened`
- `aurora-dx-asus-nvidia-userns-hardened`
- `kinoite-asus-userns-hardened`
- `kinoite-asus-nvidia-userns-hardened`
### Surface <sup>[source](https://github.com/ublue-os/hwe/tree/main/surface)</sup>
- `aurora-surface-hardened`
- `aurora-surface-nvidia-hardened`
- `aurora-surface-userns-hardened`
- `aurora-surface-nvidia-userns-hardened`
- `aurora-dx-surface-userns-hardened`
- `aurora-dx-surface-nvidia-userns-hardened`
## Server
- `securecore-main-hardened`
- `securecore-nvidia-hardened`
- `securecore-zfs-main-hardened`
- `securecore-zfs-nvidia-hardened`
- `securecore-main-userns-hardened`
- `securecore-nvidia-userns-hardened`
- `securecore-zfs-main-userns-hardened`
- `securecore-zfs-nvidia-userns-hardened`
  
# Post-install

After installation, [yafti](https://github.com/ublue-os/yafti) will open. Make sure to follow the steps listed carefully and read the directions closely.

Then follow the [POSTINSTALL-README](POSTINSTALL-README.md).

# Contributing

Follow the [contributing documentation](CONTRIBUTING.md#contributing), and make sure to respect the [CoC](CODE_OF_CONDUCT.md).

## Development

For local Development [building locally](CONTRIBUTING.md#building-locally) is the recommended approach.

## Community 
Opening issues is preferred, but [Discord](https://discord.gg/qMTv5cKfbF) is available as well.
