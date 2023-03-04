# Starting point

[![build-ublue](https://github.com/ublue-os/startingpoint/actions/workflows/build.yml/badge.svg)](https://github.com/ublue-os/startingpoint/actions/workflows/build.yml)

A starting point for creating your own customized Ostree Native Container image.

## What is this?

This is a starting point Fedora Silverblue image designed to be customized to whatever you want, have GitHub build it for you, and then host it for you. You then just tell your computer to boot off of that image. GitHub keeps 90 days worth image backups for you, thanks Microsoft!

Check out the [spec for Fedora](https://fedoraproject.org/wiki/Changes/OstreeNativeContainerStable) for more information and proper explanation.

You can use any other native container image as a base for your custom image. Check out the [uBlue images list](https://ublue.it/images/) to decide what to use!

The Github actions and methods are meant to be shared and improved upon, [so come on in](https://github.com/orgs/ublue-os/discussions) and help out!

## Making your own

See [the documentation](https://ublue.it/making-your-own/) on how to clone and use this repo for your own projects.

## Customization

You can customize this image to your needs by adding packages to install in the `recipe.yml`, configuration files in the `etc` or `usr` folders or doing any custom commands you want to in the `Containerfile`.

## Installation

> **Warning**
> This is an experimental feature and should not be used in production, try it in a VM for a while! If you are rebasing and not doing a clean install do a `touch ~/.config/ublue/firstboot-done` to keep your flatpak configuration untouched BEFORE you rebase, otherwise we're going to mangle it (for science).

> **Note**
> In the commands below, make sure to replace `ublue-os/startingpoint` with the details of your own repository.

To rebase an existing Silverblue/Kinoite installation to the latest build:

```
sudo rpm-ostree rebase ostree-unverified-registry:ghcr.io/ublue-os/startingpoint:latest
```

This repository builds date tags as well, so if you want to rebase to a particular day's build:

```
sudo rpm-ostree rebase ostree-unverified-registry:ghcr.io/ublue-os/startingpoint:20221217
```

The `latest` tag will automatically point to the latest build. Note that when a new version of Fedora is released that the `latest` tag will get updated to that latest release automatically.

## Just

The `just` task runner is included in main for further customization after first boot.
The firstboot script copies the justfile from `/etc/justfile` to your home directory.
After that run the following commands:

- `just` - Show all tasks, more will be added in the future
- `just bios` - Reboot into the system bios (Useful for dualbooting)
- `just changelogs` - Show the changelogs of the pending update
- Set up distroboxes for the following images:
  - `just distrobox-boxkit`
  - `just distrobox-debian`
  - `just distrobox-opensuse`
  - `just distrobox-ubuntu`
- `just setup-flatpaks` - Install all of the flatpaks declared in recipe.yml
- `just setup-gaming` - Install Steam, Heroic Game Launcher, OBS Studio, Discord, Boatswain, Bottles, and ProtonUp-Qt. MangoHud is installed and enabled by default, hit right Shift-F12 to toggle
- `just update` - Update rpm-ostree, flatpaks, and distroboxes in one command

Check the [just website](https://just.systems) for tips on modifying and adding your own recipes.

## Verification

These images are signed with sisgstore's [cosign](https://docs.sigstore.dev/cosign/overview/). You can verify the signature by downloading the `cosign.pub` key from this repo and running the following command:

    cosign verify --key cosign.pub ghcr.io/ublue-os/base

If you're forking this repo you should [read the docs](https://docs.github.com/en/actions/security-guides/encrypted-secrets) on keeping secrets in github. You need to [generate a new keypair](https://docs.sigstore.dev/cosign/overview/) with cosign. The public key can be in your public repo (your users need it to check the signatures), and you can paste the private key in Settings -> Secrets -> Actions.
