# secureblue

[![secureblue](https://github.com/secureblue/secureblue/actions/workflows/build.yml/badge.svg)](https://github.com/secureblue/secureblue/actions/workflows/build.yml)

## What

This repo takes the uBlue starting point and selectively applies some hardening so as to provide images that are partially hardened without sacrificing usability for most use cases. These builds may be somewhat less performant due to the performance hit of some of the applied hardening.

- Setting numerous hardened sysctl values (Inspired by but not the same as Kicksecure's)
- Disabling coredumps in limits.conf
- Disabling all ports and services for firewalld
- Blacklisting numerous unused kernel modules to reduce attack surface
- Setting more restrictive file permissions (Based on recommendations from [lynis](https://cisofy.com/lynis/))
- Installing dnf-automatic and chkrootkit
- Disabling unprivileged user namespaces and removing flatpak
- Sets numerous hardening kernel parameters (Inspired by [Madaidan's Hardening Guide](https://madaidans-insecurities.github.io/guides/linux-hardening.html))
- Installs and enables [hardened_malloc](https://github.com/GrapheneOS/hardened_malloc) globally
- Installing Chromium from the koji updates-testing repo to always have the latest version of chromium, the stable chromium package lags behind on security patches ([Why chromium?](https://madaidans-insecurities.github.io/firefox-chromium.html))
- Opinionated "debloating"

## Why

Fedora is one of the few distributions that ships with selinux and associated tooling built-in and enabled by default. This makes it advantageous as a starting point for building a hardened system. However, out of the box it's lacking hardening in numerous other areas. This project's goal is to improve on that significantly.


For more info on uBlue, check out the [uBlue homepage](https://universal-blue.org/) and the [main uBlue repo](https://github.com/ublue-os/main/)

## Installation

> **Warning**
> [This is an experimental feature](https://www.fedoraproject.org/wiki/Changes/OstreeNativeContainerStable) and should not be used in production, try it in a VM for a while!


### Available Images

> Note: gaming utilities like Steam and Lutris are not included and in my experience are largely incompatible with hardened_malloc

- kinoite-main-hardened
- kinoite-nvidia-hardened
- silverblue-main-hardened
- silverblue-nvidia-hardened


### Rebasing

To rebase an existing Silverblue/Kinoite installation to the latest build:

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
### Post-install

The following command is available to append kernel boot parameters that apply additional hardening (reboot required):

```
just set-kargs-hardening 
```

## Contributing

Follow the [contributing documentation](CONTRIBUTING.md#contributing), and make sure to respect the [CoC](CODE_OF_CONDUCT.md).

### Development

For local Development [building locally](CONTRIBUTING.md#building-locally) is the recommended approach.