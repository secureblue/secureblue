# Configuring your image

The main file of your is *the recipe file*. You can have multiple recipe files, and the ones to build are declared in the matrix section of [build.yml](../.github/workflows/build.yml). 

## Basic options

At the top of the recipe, there are four mandatory configuration options.

`name:` is the name of the image that is used when rebasing to it. For example, the name "sapphire" would result in the final URL of the container being `ghcr.io/<yourusername>/sapphire`.

`description:` is a short description of your image that will be attached to your image's metadata. 

`base-image:` is the URL of the image your image will be built upon. 

`image-version:` is the version tag of the `base-image` that will be pulled. For example, Universal Blue's images build with Fedora version tags (`38`, `39`), with the `latest` tag for the latest major version, and [many other tags](https://github.com/ublue-os/main/pkgs/container/base-main/versions?filters%5Bversion_type%5D=tagged).

## Modules

The core of startingpoint's configuration is built around the idea of modules. To be continued...