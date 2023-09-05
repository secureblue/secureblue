# [`bling`](https://github.com/ublue-os/bling) Module for Startingpoint

The `bling` module allows you to easily declare which general parts of `ublue-os/bling` to pull in to your custom image. It requires the `rpms` and `files` directories from the `bling` container to already exist inside `/tmp/bling/` (pulled inside the Containerfile by default).

The blingbling to pull in is declared under `install:`, and the code for installing them is all in simple named scripts under the `installers/` directory. The basic code for the `bling` module is very similar to the code of the `script` module.

## Example configuration:

```yml
type: bling # configure what to pull in from ublue-os/bling
install:
    - fonts # selection of common good free fonts
    - justfiles # add "!include /usr/share/ublue-os/just/bling.just"
                # in your custom.just (added by default) or local justfile
    - nix-installer # these are the silverblue nix installer scripts from dnkmmr69420
    - ublue-os-wallpapers
    # - ublue-update # https://github.com/ublue-os/ublue-update
    # - dconf-update-service # a service unit that updates the dconf db on boot
    # - devpod # https://devpod.sh/ as an rpm
```
