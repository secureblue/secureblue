<p align="center">
  <a href="https://github.com/secureblue/secureblue">
    <img src="https://github.com/secureblue/secureblue/assets/129108030/292e0ecc-50b8-4de5-a11a-bfe292489f6c" href="https://github.com/secureblue/secureblue" width=180 />
  </a>
</p>

<h1 align="center">secureblue</h1>


[![secureblue](https://github.com/secureblue/secureblue/actions/workflows/build.yml/badge.svg)](https://github.com/secureblue/secureblue/actions/workflows/build.yml)
[![Discord](https://img.shields.io/discord/1202086019298500629?style=flat&logo=discord&logoColor=white&label=Discord&labelColor=%235F6AE9&color=%2333CB56)
](https://discord.com/invite/qMTv5cKfbF)

This repo uses [BlueBuild](https://blue-build.org/) to generate hardened operating system images, using [uBlue](https://universal-blue.org)'s [Fedora Atomic](https://fedoraproject.org/atomic-desktops/)-based [base images](https://github.com/orgs/ublue-os/packages?repo_name=main) as a starting point. This hardening is done with the following goals in mind:

- Increase defenses against the exploitation of both known and unknown vulnerabilities.
- Avoid sacrificing usability for most use cases where possible

The following are not in scope for this project:
- Anything related to "privacy", since Fedora is already sufficiently private and "privacy" often serves as a euphemism for security theater. This is especially true when at odds with improving security.
- Anything related to "degoogling" chromium. For example, we will not be replacing chromium with Brave or ungoogled-chromium.

## What

Hardening applied:

- Setting numerous hardened sysctl values (Inspired by but not the same as Kicksecure's) <sup>[details](https://github.com/secureblue/secureblue/blob/live/config/files/usr/etc/sysctl.d/hardening.conf)</sup>
- Disabling coredumps in limits.conf
- Disabling all ports and services for firewalld
- Adds per-network MAC randomization
- Blacklisting numerous unused kernel modules to reduce attack surface <sup>[details](https://github.com/secureblue/secureblue/blob/live/config/files/usr/etc/modprobe.d/blacklist.conf)</sup>
- Enabling only the [flathub-verified](https://flathub.org/apps/collection/verified/1) remote by default
- Sets numerous hardening kernel parameters (Inspired by [Madaidan's Hardening Guide](https://madaidans-insecurities.github.io/guides/linux-hardening.html)) <sup>[details](https://github.com/secureblue/secureblue/blob/live/config/files/usr/share/ublue-os/just/60-custom.just.readme.md)</sup>
- Installs and enables [hardened_malloc](https://github.com/GrapheneOS/hardened_malloc) globally, including for flatpaks. <sup>[Thanks to rusty-snake's hardened_malloc spec](https://github.com/rusty-snake/fedora-extras)</sup>
- Installing Chromium instead of Firefox in the base image <sup>[Why chromium?](https://grapheneos.org/usage#web-browsing)</sup> <sup>[Why not flatpak chromium?](https://forum.vivaldi.net/post/669805)</sup>
- Including a hardened chromium config <sup>[vanadium comparison](https://github.com/secureblue/secureblue/blob/live/config/files/usr/etc/chromium/vanadium_comparison.readme.md)</sup> that sets numerous hardened defaults <sup>[details](https://github.com/secureblue/secureblue/blob/live/config/files/usr/etc/chromium/policies/managed/hardening.json.readme.md)</sup> and disables JIT javascript <sup>[why?](https://microsoftedge.github.io/edgevr/posts/Super-Duper-Secure-Mode/#is-jit-worth-it)</sup>
- Pushing upstream fedora to harden the build for all fedora users, including secureblue users ([for example, by enabling CFI](https://bugzilla.redhat.com/show_bug.cgi?id=2252874))
- Reduce the sudo timeout to 1 minute
- Disable passwordless sudo for `rpm-ostree install` <sup>[why?](https://github.com/rohanssrao/silverblue-privesc)
- Brute force protection by locking user accounts for 24 hours after 50 failed login attempts, hardened password encryption and password quality suggestions
- Installing usbguard and bubblejail
- Set opportunistic DNSSEC and DNSOverTLS for systemd-resolved
- Configure chronyd to use Network Time Security (NTS) <sup>[using chrony config from GrapheneOS](https://github.com/GrapheneOS/infrastructure/blob/main/chrony.conf)</sup>
- Disable KDE GHNS by default <sup>[why?](https://blog.davidedmundson.co.uk/blog/kde-store-content/)</sup>
- (Non-userns variants) Disabling unprivileged user namespaces
- (Non-userns variants) Replacing bubblewrap with bubblewrap-suid so flatpak can be used without unprivileged user namespaces

## Why

Fedora is one of the few distributions that ships with selinux and associated tooling built-in and enabled by default. This makes it advantageous as a starting point for building a hardened system. However, out of the box it's lacking hardening in numerous other areas. This project's goal is to improve on that significantly.


For more info on uBlue and BlueBuild, check out the [uBlue homepage](https://universal-blue.org/) and the [BlueBuild homepage](https://blue-build.org/).

## Customization

If you want to add your own customizations on top of secureblue, you are advised strongly against forking. Instead, create a repo for your own image by using the [BlueBuild template](https://github.com/blue-build/template), then change your `base-image` to a secureblue image. This will allow you to apply your customizations to secureblue in a concise and maintainable way, without the need to constantly sync with upstream. 

## FAQ

[FAQ](FAQ.md)

## Installation

Have a look at [PREINSTALL-README](PREINSTALL-README.md) before proceeding.

### Rebasing (Recommended)

To rebase a Fedora Atomic installation, choose an $IMAGE_NAME from the [list below](README.md#available-images), then follow these steps:

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

### ISO 

While it's recommended to use a Fedora Atomic iso to install and then rebase that installation to secureblue, you can also generate an iso and install that directly using [this script](generate_secureblue_iso.sh). Please note you should still follow the [post-install steps](README.md#post-install) when installing from a generated iso:

```
./generate_secureblue_iso.sh
```

### Available Images

#### Without User Namespaces <sup>[What's the difference?](USERNS.md)</sup>

##### general purpose
###### stable
- kinoite-main-hardened
- kinoite-nvidia-hardened
- bluefin-main-hardened
- bluefin-nvidia-hardened
- aurora-main-hardened
- aurora-nvidia-hardened
- silverblue-main-hardened
- silverblue-nvidia-hardened
- sericea-main-hardened
- sericea-nvidia-hardened

###### experimental
- cinnamon-main-hardened
- cinnamon-nvidia-hardened
- wayblue-wayfire-main-hardened
- wayblue-wayfire-nvidia-hardened
- wayblue-hyprland-main-hardened
- wayblue-hyprland-nvidia-hardened
- wayblue-river-main-hardened
- wayblue-river-nvidia-hardened
- wayblue-sway-main-hardened
- wayblue-sway-nvidia-hardened


##### surface <sup>[source](https://github.com/ublue-os/hwe/tree/main/surface)</sup>

- aurora-surface-hardened
- aurora-surface-nvidia-hardened

##### asus <sup>[source](https://github.com/ublue-os/hwe/tree/main/asus)</sup>
- aurora-asus-hardened
- aurora-asus-nvidia-hardened
- silverblue-asus-hardened
- silverblue-asus-nvidia-hardened
- kinoite-asus-hardened
- kinoite-asus-nvidia-hardened

##### server
- server-main-hardened
- server-nvidia-hardened

#### With User Namespaces <sup>[What's the difference?](USERNS.md)</sup>

##### general purpose
###### stable
- kinoite-main-userns-hardened
- kinoite-nvidia-userns-hardened
- bluefin-dx-main-userns-hardened
- bluefin-dx-nvidia-userns-hardened
- bluefin-main-userns-hardened
- bluefin-nvidia-userns-hardened
- aurora-main-userns-hardened
- aurora-nvidia-userns-hardened
- aurora-dx-main-userns-hardened
- aurora-dx-nvidia-userns-hardened
- silverblue-main-userns-hardened
- silverblue-nvidia-userns-hardened
- sericea-main-userns-hardened
- sericea-nvidia-userns-hardened

###### experimental
- cinnamon-main-userns-hardened
- cinnamon-nvidia-userns-hardened
- wayblue-wayfire-main-userns-hardened
- wayblue-wayfire-nvidia-userns-hardened
- wayblue-hyprland-main-userns-hardened
- wayblue-hyprland-nvidia-userns-hardened
- wayblue-river-main-userns-hardened
- wayblue-river-nvidia-userns-hardened
- wayblue-sway-main-userns-hardened
- wayblue-sway-nvidia-userns-hardened

##### surface <sup>[source](https://github.com/ublue-os/hwe/tree/main/surface)</sup>

- aurora-surface-userns-hardened
- aurora-surface-nvidia-userns-hardened
- aurora-dx-surface-userns-hardened
- aurora-dx-surface-nvidia-userns-hardened

##### asus <sup>[source](https://github.com/ublue-os/hwe/tree/main/asus)</sup>
- aurora-asus-userns-hardened
- aurora-asus-nvidia-userns-hardened
- aurora-dx-asus-userns-hardened
- aurora-dx-asus-nvidia-userns-hardened
- silverblue-asus-userns-hardened
- silverblue-asus-nvidia-userns-hardened
- kinoite-asus-userns-hardened
- kinoite-asus-nvidia-userns-hardened

##### server
- server-main-userns-hardened
- server-nvidia-userns-hardened
  
### Post-install

After installation, [yafti](https://github.com/ublue-os/yafti) will open. Make sure to follow the steps listed carefully and read the directions closely.

Have a look at [POSTINSTALL-README](POSTINSTALL-README.md).

#### Nvidia
If you are using an nvidia image, run this after installation:

```
rpm-ostree kargs \
    --append-if-missing=rd.driver.blacklist=nouveau \
    --append-if-missing=modprobe.blacklist=nouveau \
    --append-if-missing=nvidia-drm.modeset=1
```

#### Nvidia optimus laptop
If you are using an nvidia image on an optimus laptop, run this after installation:

```
ujust configure-nvidia-optimus
```


## Contributing

Follow the [contributing documentation](CONTRIBUTING.md#contributing), and make sure to respect the [CoC](CODE_OF_CONDUCT.md).

### Development

For local Development [building locally](CONTRIBUTING.md#building-locally) is the recommended approach.

### Community 
Opening issues is preferred, but [Discord](https://discord.gg/qMTv5cKfbF) is available as well.
