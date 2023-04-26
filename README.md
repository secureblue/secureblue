# Starting point

[![build-ublue](https://github.com/ublue-os/startingpoint/actions/workflows/build.yml/badge.svg)](https://github.com/ublue-os/startingpoint/actions/workflows/build.yml)

This is a starting point Fedora Silverblue image designed to be customized to whatever you want, have GitHub build it for you, and then host it for you. You then just tell your computer to boot off of that image. GitHub keeps 90 days worth image backups for you, thanks Microsoft!

For more info, check out the [uBlue homepage](https://ublue.it/) and the [main uBlue repo](https://github.com/ublue-os/main/)

## Getting started

See the [Make Your Own -page in the documentation](https://ublue.it/making-your-own/) for quick setup instructions for setting up your own repository based on this template.

Don't worry, it only requires some basic knowledge about using the terminal and git.

> **Note**
> Everywhere in this repository, make sure to replace `ublue-os/startingpoint` with the details of your own repository. Unless you used [`create-ublue-image`](https://github.com/EinoHR/create-ublue-image), in which case the previous repo identifier should already be your repo's details.

## Customization

The easiest way to start customizing is by looking at and modifying `recipe.yml`. It's documented using comments and should be pretty easy to understand.

For the base-image field, you can use any other native container image. You will get all the features of that image, plus the ones added here! Check out the [uBlue images list](https://ublue.it/images/) to decide what to use!

If you want to add custom configuration files, you can just add them in the `etc` directory. If you need to add other directories, you can look at the Containerfile to see how it's done. Writing to any directories under `/var` in Fedora Silverblue are not supported and will not work, as those are user-managed.

> **Note**
> The configuration files you put in the `etc` directory are actually added to `/usr/etc/` where they get applied to your local `/etc/` when rebasing to or updating the image. If a config file in `/etc/` has been changed, the changes won't be overridden, but the new version will be available in `/usr/etc/`. Run `sudo ostree admin config-diff` to see the difference between `/etc/` and `/usr/etc/` (`man ostree-admin-config-diff` for further documentation).

### Custom build scripts

If you want to execute custom shell script or commands in the image build, you shouldn't edit `build.sh` or the `Containerfile` directly. Instead, you can create a shell script in the `scripts/` directory (look at the `example.sh`). After creating your script, enable it in the `scripts:` section of your `recipe.yml`.

### Building multiple images

You can build multiple images using multiple `recipe.yml` files. They will share the Containerfile and everything else, but things like packages declared in the recipe will be different between the images. For a more robust multibuild setup, you could consider forking from the [ublue-os/main](https://github.com/ublue-os/main/) repo, which was built from the purpose.

In order to build multiple recipes, you need to declare each one below line ~33 in `build.yml`. The files should be in the root of the repository.

Example: Adding a new recipe called `recipe-2.yml` (snippets from the `matrix` section of `build.yml`)

Before:

```yml
matrix:
  recipe:
    - recipe.yml
```

After:

```yml
matrix:
  recipe:
    - recipe.yml
    - recipe-2.yml
```

### [yafti](https://github.com/ublue-os/yafti/)

`yafti` is the uBlue firstboot installer, and it's configuration can be found in `/etc/yafti.yml`. It includes an optional selection of Flatpaks to install, with a new group added for the Flatpaks declared in `recipe.yml`. You can look at what's done in the config and modify it to your liking.

The files `/etc/profile.d/ublue-firstboot.sh` and `/etc/skel.d/.config/autostart/ublue-firstboot.desktop` set up `yafti` so that it starts on boot, so if you wish to retain that functionality those files shouldn't be touched.

## Installation

> **Warning**
> This is an experimental feature and should not be used in production, try it in a VM for a while!

To rebase an existing Silverblue/Kinoite installation to the latest build:

```
sudo rpm-ostree rebase ostree-unverified-registry:ghcr.io/ublue-os/startingpoint:latest
```

This repository builds date tags as well, so if you want to rebase to a particular day's build:

```
sudo rpm-ostree rebase ostree-unverified-registry:ghcr.io/ublue-os/startingpoint:20230403
```

The `latest` tag will automatically point to the latest build. That build will still always use the Fedora version specified in `release.yml`, so you won't get accidentally updated to the next major version.

## Just

The `just` task runner is included in main for further customization after first boot.
You can copy the justfile from `/etc/justfile` to `~/.justfile` to get started. Once `just` supports [include directives](https://just.systems/man/en/chapter_52.html), you can just include the file in `/etc` into your own justfile, where you have the option of adding new tasks.
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

    cosign verify --key cosign.pub ghcr.io/ublue-os/startingpoint

If you're forking this repo, the uBlue website has [instructions](https://ublue.it/making-your-own/) for setting up signing properly.
