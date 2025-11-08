# brewdirect

The brew module installs [Homebrew / Linuxbrew](https://brew.sh/) on your system and ensures the package manager remains updated and maintained. This module also sets up systemd services to periodically update the installed Brew packages.

## Features
- Downloads Brew in build-time & installs it in run-time.
- Sets up systemd services to automatically update Brew to the latest version.
- Sets up systemd services to automatically upgrade Brew packages.
- Sets up bash and fish completions for Brew.

## How it works

### Build-time:

- Necessary Brew package dependency `gcc` & `zstd` is installed if not present in the base image.
- Brew tarball is downloaded from [Universal Blue 'packages' GitHub releases](https://github.com/ublue-os/packages/releases).
- Brew tarball is extracted to `/usr/share/homebrew/`.
- `/usr/share/homebrew/` permissions are set to the default user (UID/GID 1000).
- `brew-update` & `brew-upgrade` SystemD service timers are enabled (by default).
- A fix for path conflicts between system & brew packages with the same name is applied by adding Brew to path only in interactive shells, unlike what Brew does by default.
- Set option that Brew's shell environment can't be ran as root, respecting Homebrew's recommendation that only user with UID/GID 1000 can manage Brew.
- Brew bash & fish shell completions are copied to `/etc/profile.d/brew-bash-completions.sh` & `/usr/share/fish/vendor_conf.d/brew-fish-completions.fish`.
- `tmpfiles.d` configuration `homebrew.conf` is written with these directory locations:
  - `/var/lib/homebrew/`
  - `/var/cache/homebrew/`
  - `/home/linuxbrew/`
- `brew-setup` service is enabled.

### Run-time:

**`tmpfiles.d homebrew.conf`:**
- This configuration is telling SystemD to: automatically create these necessary directories on every system boot if not available & to give them permissions of the default user (UID 1000):
  - `/var/lib/homebrew/`
  - `/var/cache/homebrew/`
  - `/home/linuxbrew/`

**`brew-setup`:**
- `brew-setup` installs `brew` in runtime.  
  SystemD service checks if main directory used by Brew exists (`/home/linuxbrew/.linuxbrew/`) & if `brew-setup` state file exists (`/etc/.linuxbrew`).
- If one of those paths don't exist, then extracted Brew tarball is copied from `/usr/share/homebrew/` to `/home/linuxbrew/`.
- Permissions to `/home/linuxbrew/` are set to the default user (UID/GID 1000).
- Empty file `/etc/.linuxbrew` is created, which indicates that brew-setup (installation) is successful & which allows setup to run again on next boot when removed.

**Rest of the setup:**
- `brew-update` runs at the specified time to update Brew to the latest version.
- `brew-upgrade` runs at the specified time to upgrade Brew packages.  
  It additionally unlinks conflicting Brew dependencies if installed, like systemd & dbus, to prevent crucial system programs being preferred by Brew.

## Development
Setting `DEBUG=true` inside `brew.sh` will enable additional output for debugging purposes during development.

## Uninstallation

Removing the `brew` module from the recipe is not enough to get it completely removed.   
On a booted system, it's also necessary to run the `brew` uninstallation script.

Either a local-user can execute this script manually or the image-maintainer may make it automatic through a custom systemd service.

Uninstallation script:  
```bash
#!/usr/bin/env bash

# Remove Homebrew cache
if [[ -d "${HOME}/cache/Homebrew/" ]]; then
  echo "Removing '$HOME/cache/Homebrew/' directory"
  rm -r "${HOME}/cache/Homebrew/"
else
  echo "'${HOME}/cache/Homebrew/' directory is already removed"
fi

# Remove folders created by tmpfiles.d
if [[ -d "/var/lib/homebrew/" ]]; then
  echo "Removing '/var/lib/homebrew/' directory"
  sudo rm -rf "/var/lib/homebrew/"
else
  echo "'/var/lib/homebrew/' directory is already removed"
fi
if [[ -d "/var/cache/homebrew/" ]]; then
  echo "Removing '/var/cache/homebrew/' directory"
  sudo rm -rf "/var/cache/homebrew/"
else
  echo "'/var/cache/homebrew/' directory is already removed"
fi
## This is the main directory where brew is located
if [[ -d "/var/home/linuxbrew/" ]]; then
  echo "Removing '/home/linuxbrew/' directory"
  sudo rm -rf "/var/home/linuxbrew/"
else
  echo "'/home/linuxbrew/' directory is already removed"
fi

# Remove redundant brew-setup service state file
if [[ -f "/etc/.linuxbrew" ]]; then
  echo "Removing empty '/etc/.linuxbrew' file"
  sudo rm -f "/etc/.linuxbrew"
else
  echo "'/etc/.linuxbrew' file is already removed"
fi
```

## Credits

Thanks a lot to Bluefin custom image maintainer [m2giles](https://github.com/m2Giles), who made this entire module possible.  
In fact, the module's logic of installing & updating/upgrading Brew is fully copied from him & Bluefin, we just made it easier & more convenient to use for BlueBuild users.
