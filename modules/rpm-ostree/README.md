# [`rpm-ostree`](https://coreos.github.io/rpm-ostree/) Module for Startingpoint

The `rpm-ostree` module offers pseudo-declarative package and repository management using `rpm-ostree`.

The module first downloads the repository files from repositories declared under `repos:` into `/etc/yum.repos.d/`. The magic string `%OS_VERSION%` is substituted with the current VERSION_ID (major Fedora version), which can be used, for example, for pulling correct versions of repositories from [Fedora's Copr](https://copr.fedorainfracloud.org/).

Then the module installs the packages declared under `install:` using `rpm-ostree install`, it removes the packages declared under `remove:` using `rpm-ostree override remove`. If there are packages declared under both `install:` and `remove:` a hybrid command `rpm-ostree remove <packages> --install <packages>` is used, which should allow you to switch required packages for other ones.

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


## Known issues

When removing certain packages, some problem probably in upstream `rpm-ostree` causes a `depsolve` issue similar to below. [Removed packages are still present in the underlying ostree repository](https://coreos.github.io/rpm-ostree/administrator-handbook/#removing-a-base-package), what `remove` does is "hide" them from the system, it doesn't reclaim disk space.
```
Resolving dependencies...done
error: Could not depsolve transaction; 1 problem detected:
Problem: conflicting requests
```