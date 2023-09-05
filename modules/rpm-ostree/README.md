# [`rpm-ostree`](https://coreos.github.io/rpm-ostree/) Module for Startingpoint

The `rpm-ostree` module offers pseudo-declarative package and repository management using `rpm-ostree`.

The module first downloads the repository files from repositories declared under `repos:` into `/etc/yum.repos.d/`. The magic string `%OS_VERSION%` is substituted with the current VERSION_ID (major Fedora version), which can be used, for example, for pulling correct versions of repositories from [Fedora's Copr](https://copr.fedorainfracloud.org/).

Then the module installs the packages declared under `install:` using `rpm-ostree install`, and lastly, it removes the packages declared under `remove:` using `rpm-ostree override remove`.

Additionally, the `rpm-ostree` module supports a temporary (waiting for `rpm-ostree` issue [#233](https://github.com/coreos/rpm-ostree/issues/233)) fix for packages that install into `/opt/`. Installation for packages that install into folder names declared under `optfix:` are fixed using some symlinks.

## Example Configuration:

```yml
type: rpm-ostree
repos:
  - https://copr.fedorainfracloud.org/coprs/atim/starship/repo/fedora-%OS_VERSION%/atim-starship-fedora-%OS_VERSION%.repo
install:
  - python3-pip
  - libadwaita
remove:
  - firefox
  - firefox-langpacks
```
