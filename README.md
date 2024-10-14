<p align="center">
  <a href="https://github.com/secureblue/secureblue">
    <img src="https://github.com/secureblue/secureblue/assets/129108030/292e0ecc-50b8-4de5-a11a-bfe292489f6c" href="https://github.com/secureblue/secureblue" width=180 />
  </a>
</p>

<h1 align="center">secureblue</h1>


[![secureblue](https://github.com/secureblue/secureblue/actions/workflows/build.yml/badge.svg)](https://github.com/secureblue/secureblue/actions/workflows/build.yml)
[![Discord](https://img.shields.io/discord/1202086019298500629?style=flat&logo=discord&logoColor=white&label=Discord&labelColor=%235F6AE9&color=%2333CB56)](https://discord.com/invite/qMTv5cKfbF)
[![Donate](https://img.shields.io/badge/Donate-blue.svg)](https://github.com/secureblue/secureblue/blob/live/DONATE.md)

This repo uses [BlueBuild](https://blue-build.org/) to generate hardened operating system images, using [Fedora Atomic Desktop](https://fedoraproject.org/atomic-desktops/)'s [base images](https://pagure.io/workstation-ostree-config) as a starting point.

# Scope

secureblue applies hardening with the following goals in mind:

- Increase defenses against the exploitation of both known and unknown vulnerabilities.
- Avoid sacrificing usability for most use cases where possible

The following are not in scope:
- Anything that sacrifices security for "privacy". Fedora is already sufficiently private and "privacy" often serves as a euphemism for security theater. This is especially true when at odds with improving security.
- Anything related to "degoogling" chromium. For example, we will not be replacing [hardened-chromium](https://github.com/secureblue/hardened-chromium) with Brave or ungoogled-chromium. Both of them make changes that sacrifice security for "privacy", such as enabling MV2. <sup>[why?](https://developer.chrome.com/docs/extensions/develop/migrate/improve-security)</sup>

# Hardening

- Installing and enabling [hardened_malloc](https://github.com/GrapheneOS/hardened_malloc) globally, including for flatpaks. <sup>[Thanks to rusty-snake's spec](https://github.com/rusty-snake/fedora-extras)</sup>
- Installing [hardened-chromium](https://github.com/secureblue/hardened-chromium), which is inspired by [Vanadium](https://github.com/GrapheneOS/Vanadium). <sup>[Why chromium?](https://grapheneos.org/usage#web-browsing)</sup> <sup>[Why not flatpak chromium?](https://forum.vivaldi.net/post/669805)</sup>
- Setting numerous hardened sysctl values <sup>[details](https://github.com/secureblue/secureblue/blob/live/files/system/etc/sysctl.d/hardening.conf)</sup>
- Remove SUID-root from [numerous binaries](https://github.com/secureblue/secureblue/blob/live/files/scripts/removesuid.sh) and replace functionality [using capabilities](https://github.com/secureblue/secureblue/blob/live/files/system/usr/bin/setcapsforunsuidbinaries)
- Disable Xwayland by default (for GNOME, Plasma, and Sway images)
- Mitigation of [LD_PRELOAD attacks](https://github.com/Aishou/wayland-keylogger) via `ujust toggle-bash-environment-lockdown`
- Disabling coredumps 
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
- Disable a variety of services by default (including cups, geoclue, passim, and others)
- Removal of the unmaintained and suid-root fuse2 by default
- (Non-userns variants) Disabling unprivileged user namespaces
- (Non-userns variants) Replacing bubblewrap with suid-root bubblewrap so flatpak can be used without unprivileged user namespaces

# Rationale

Fedora is one of the few distributions that ships with selinux and associated tooling built-in and enabled by default. This makes it advantageous as a starting point for building a hardened system. However, out of the box it's lacking hardening in numerous other areas. This project's goal is to improve on that significantly.


For more info on BlueBuild, check out the [BlueBuild homepage](https://blue-build.org/).

# Customization

If you want to add your own customizations on top of secureblue, you are advised strongly against forking. Instead, create a repo for your own image by using the [BlueBuild template](https://github.com/blue-build/template), then change your `base-image` to a secureblue image. This will allow you to apply your customizations to secureblue in a concise and maintainable way, without the need to constantly sync with upstream. 

# FAQ

If you're encountering a problem or have a question, please consult the [FAQ](FAQ.md). If you can't find your answer there, please ask in the support channel on Discord.

# Sponsor

Sponsorship options are on the [Donate](DONATE.md) page. All donations are appreciated. Sponsors get a role on the Discord if desired. If you've donated but haven't yet been tagged with the role, please reach out to me.

# Installation

Have a look at [PREINSTALL-README](PREINSTALL-README.md) before proceeding.

## Rebasing (Recommended)

To rebase a [Fedora Atomic](https://fedoraproject.org/atomic-desktops/) installation, choose an $IMAGE_NAME from the [list below](README.md#images-userns), then follow these steps:

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

# Images

*Note: Learn about unprivileged user namespaces [here](USERNS.md).*

## Desktop

### Recommended <sup>[why?](RECOMMENDED.md)</sup>

| Name                                      | Base      | Nvidia Support | Unprivileged User Namespaces |
|-------------------------------------------|-----------|----------------|------------------------------|
| `silverblue-main-hardened`               | Silverblue| No             | No     |
| `silverblue-nvidia-hardened`             | Silverblue| Yes            | No     |
| `silverblue-main-userns-hardened`        | Silverblue| No             | Yes    |
| `silverblue-nvidia-userns-hardened`      | Silverblue| Yes            | Yes    |

### Stable
| Name                                      | Base      | Nvidia Support | Unprivileged User Namespaces |
|-------------------------------------------|-----------|----------------|------------------------------|
| `kinoite-main-hardened`                  | Kinoite   | No             | No     |
| `kinoite-nvidia-hardened`                | Kinoite   | Yes            | No     |
| `kinoite-main-userns-hardened`           | Kinoite   | No             | Yes    |
| `kinoite-nvidia-userns-hardened`         | Kinoite   | Yes            | Yes    |
| `sericea-main-hardened`                  | Sericea   | No             | No     |
| `sericea-nvidia-hardened`                | Sericea   | Yes            | No     |
| `sericea-main-userns-hardened`           | Sericea   | No             | Yes    |
| `sericea-nvidia-userns-hardened`         | Sericea   | Yes            | Yes    |

### Beta  <sup>[wayblue?](https://github.com/wayblueorg/wayblue)</sup>
| Name                                      | Base      | Nvidia Support | Unprivileged User Namespaces |
|-------------------------------------------|-----------|----------------|------------------------------|
| `wayblue-wayfire-main-hardened`          | Wayblue   | No             | No     |
| `wayblue-wayfire-nvidia-hardened`        | Wayblue   | Yes            | No     |
| `wayblue-wayfire-main-userns-hardened`   | Wayblue   | No             | Yes    |
| `wayblue-wayfire-nvidia-userns-hardened` | Wayblue   | Yes            | Yes    |
| `wayblue-hyprland-main-hardened`         | Wayblue   | No             | No     |
| `wayblue-hyprland-nvidia-hardened`       | Wayblue   | Yes            | No     |
| `wayblue-hyprland-main-userns-hardened`  | Wayblue   | No             | Yes    |
| `wayblue-hyprland-nvidia-userns-hardened`| Wayblue   | Yes            | Yes    |
| `wayblue-river-main-hardened`            | Wayblue   | No             | No     |
| `wayblue-river-nvidia-hardened`          | Wayblue   | Yes            | No     |
| `wayblue-river-main-userns-hardened`     | Wayblue   | No             | Yes    |
| `wayblue-river-nvidia-userns-hardened`   | Wayblue   | Yes            | Yes    |
| `wayblue-sway-main-hardened`             | Wayblue   | No             | No     |
| `wayblue-sway-nvidia-hardened`           | Wayblue   | Yes            | No     |
| `wayblue-sway-main-userns-hardened`      | Wayblue   | No             | Yes    |
| `wayblue-sway-nvidia-userns-hardened`    | Wayblue   | Yes            | Yes    |

## Server

| Name                                      | Base      | Nvidia Support | ZFS Support | Unprivileged User Namespaces |
|-------------------------------------------|-----------|----------------|-------------|--------|
| `securecore-main-hardened`               | CoreOS    | No             | No          | No     |
| `securecore-nvidia-hardened`             | CoreOS    | Yes            | No          | No     |
| `securecore-main-userns-hardened`        | CoreOS    | No             | No          | Yes    |
| `securecore-nvidia-userns-hardened`      | CoreOS    | Yes            | No          | Yes    |
| `securecore-zfs-main-hardened`           | CoreOS    | No             | Yes         | No     |
| `securecore-zfs-nvidia-hardened`         | CoreOS    | Yes            | Yes         | No     |
| `securecore-zfs-main-userns-hardened`    | CoreOS    | No             | Yes         | Yes    |
| `securecore-zfs-nvidia-userns-hardened`  | CoreOS    | Yes            | Yes         | Yes    |

# Post-install

After installation, [yafti](https://github.com/ublue-os/yafti) will open. Make sure to follow the steps listed carefully and read the directions closely.

Then follow the [POSTINSTALL-README](POSTINSTALL-README.md).

# Contributing

Follow the [contributing documentation](CONTRIBUTING.md#contributing), and make sure to respect the [CoC](CODE_OF_CONDUCT.md).

## Development

For local Development [building locally](CONTRIBUTING.md#building-locally) is the recommended approach.

## Community 
Opening issues is preferred, but [Discord](https://discord.gg/qMTv5cKfbF) is available as well.
