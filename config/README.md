# Configuring your image

The main file of your is *the recipe file*. You can have multiple recipe files, and the ones to build are declared in the matrix section of [build.yml](../.github/workflows/build.yml). 

## Basic options

At the top of the recipe, there are four *mandatory* configuration options.

`name:` is the name of the image that is used when rebasing to it. For example, the name "sapphire" would result in the final URL of the container being `ghcr.io/<yourusername>/sapphire`.

`description:` is a short description of your image that will be attached to your image's metadata. 

`base-image:` is the URL of the image your image will be built upon. 

`image-version:` is the version tag of the `base-image` that will be pulled. For example, Universal Blue's images build with Fedora version tags (`38`, `39`), with the `latest` tag for the latest major version, and [many other tags](https://github.com/ublue-os/main/pkgs/container/base-main/versions?filters%5Bversion_type%5D=tagged).

## Modules

The core of startingpoint's configuration is built around the idea of modules. Modules are scripts in the [`../modules`](../modules/) directory that you list out under `modules:` in the recipe. They are executed in order, and can run arbitrary shell commands and write any files.

This repository fetches some useful default modules from [`ublue-os/bling`](https://github.com/ublue-os/bling/), like [`rpm-ostree`](../modules/rpm-ostree) for pseudo-declarative package management, [`bling`](../modules/bling) for pulling extra components from [`ublue-os/bling`](https://github.com/ublue-os/bling), and [`files`](../modules/files) for copying files from the `config/files/` directory into your image. For a comprehensive list of modules and their in-depth documentation, check out [the modules page on the website](https://universal-blue.org/tinker/modules/).

### Including modules from other files and building multiple images

To build multiple images, you need to create another recipe.yml file, which you should name based on what kind of image you want it to build. Then, edit the [`build.yml`](../.github/workflows/build.yml) file. Inside the file, under `jobs: strategy: matrix:`, there's a list of recipe files to build images, which you need to add your new recipe file to. These should be paths to files inside the `config` directory.

Module configuration can be included from other files using the `from-file` syntax. The valye should be a path to a file inside the `config` directory. For example, the following snippet could be used to include the configuration for installing a set of packages common to multiple images.
```yml
modules:
  - from-file: common-packages.yml
```