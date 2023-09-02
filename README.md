# hardened-images

[![hardened-images](https://github.com/qoijjj/hardened-images/actions/workflows/build.yml/badge.svg)](https://github.com/qoijjj/hardened-images/actions/workflows/build.yml)

This repo takes the uBlue starting point and selectively applies minimal hardening so as to provide images that are partially hardened without sacrificing usability for most use cases. These builds may be somewhat less performant due to the performance hit of some of the applied hardening.

For more info on uBlue, check out the [uBlue homepage](https://universal-blue.org/) and the [main uBlue repo](https://github.com/ublue-os/main/)

## Installation

> **Warning**
> This is an experimental feature and should not be used in production, try it in a VM for a while!


### Available Images

- kinoite-main-hardened
- kinoite-nvidia-hardened
- silverblue-main-hardened
- silverblue-nvidia-hardened

### Rebasing

To rebase an existing Silverblue/Kinoite installation to the latest build:


- First rebase to the image unsigned, to get the proper signing keys and policies installed:
  ```
  sudo rpm-ostree rebase ostree-unverified-registry:ghcr.io/qoijjj/$IMAGE_NAME:latest
  ```
- Reboot to complete the rebase:
  ```
  systemctl reboot
  ```
- Then rebase to the signed image, like so:
  ```
  sudo rpm-ostree rebase ostree-image-signed:docker://ghcr.io/qoijjj/$IMAGE_NAME:latest
  ```
- Reboot again to complete the installation
  ```
  systemctl reboot
  ```


This repository builds date tags as well, so if you want to rebase to a particular day's build:

```
sudo rpm-ostree rebase ostree-image-signed:docker://ghcr.io/qoijjj/$IMAGE_NAME:20230403
```

This repository by default also supports signing 

The `latest` tag will automatically point to the latest build. That build will still always use the Fedora version specified in `recipe.yml`, so you won't get accidentally updated to the next major version.