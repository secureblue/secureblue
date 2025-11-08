#!/usr/bin/env bash

set -euo pipefail

# Debugging
DEBUG="${DEBUG:-false}"
if [[ "${DEBUG}" == true ]]; then
    set -x
fi

# Check if gcc is installed & install it if it's not
# (add VanillaOS package manager in the future when it gets supported)
if ! command -v gcc &> /dev/null; then
  if command -v dnf5 &> /dev/null; then
    echo "Installing \"gcc\" package, which is necessary for Brew to function"
    dnf5 -y install gcc
  elif command -v rpm-ostree &> /dev/null; then
    echo "Installing \"gcc\" package, which is necessary for Brew to function"
    rpm-ostree install gcc
  else
    echo "ERROR: \"gcc\" package could not be found"
    echo "       Brew depends on \"gcc\" in order to function"
    echo "       Please include \"gcc\" in the list of packages to install with the system package manager"
    exit 1
  fi
fi

# Check if zstd is installed & install it if it's not
if ! command -v zstd &> /dev/null; then
  if command -v dnf5 &> /dev/null; then
    echo "Installing \"zstd\" package, which is necessary for Brew to function"
    dnf5 -y install zstd
  elif command -v rpm-ostree &> /dev/null; then
    echo "Installing \"zstd\" package, which is necessary for Brew to function"
    rpm-ostree install zstd
  else
    echo "ERROR: \"zstd\" package could not be found"
    echo "       Brew's installer depends on \"zstd\" in order to function"
    echo "       Please include \"zstd\" in the list of packages to install with the system package manager"
    exit 1
  fi
fi

# Module-specific directories and paths
MODULE_DIRECTORY="${MODULE_DIRECTORY:-/tmp/modules}"

# Configuration values
AUTO_UPDATE=$(echo "${1}" | jq -r 'try .["auto-update"]')
if [[ -z "${AUTO_UPDATE}" || "${AUTO_UPDATE}" == "null" ]]; then
    AUTO_UPDATE=true
fi

UPDATE_INTERVAL=$(echo "${1}" | jq -r 'try .["update-interval"]')
if [[ -z "${UPDATE_INTERVAL}" || "${UPDATE_INTERVAL}" == "null" ]]; then
    UPDATE_INTERVAL="6h"
fi

UPDATE_WAIT_AFTER_BOOT=$(echo "${1}" | jq -r 'try .["update-wait-after-boot"]')
if [[ -z "${UPDATE_WAIT_AFTER_BOOT}" || "${UPDATE_WAIT_AFTER_BOOT}" == "null" ]]; then
    UPDATE_WAIT_AFTER_BOOT="10min"
fi

AUTO_UPGRADE=$(echo "${1}" | jq -r 'try .["auto-upgrade"]')
if [[ -z "${AUTO_UPGRADE}" || "${AUTO_UPGRADE}" == "null" ]]; then
    AUTO_UPGRADE=true
fi

UPGRADE_INTERVAL=$(echo "$1" | jq -r 'try .["upgrade-interval"]')
if [[ -z "${UPGRADE_INTERVAL}" || "${UPGRADE_INTERVAL}" == "null" ]]; then
    UPGRADE_INTERVAL="8h"
fi

UPGRADE_WAIT_AFTER_BOOT=$(echo "${1}" | jq -r 'try .["upgrade-wait-after-boot"]')
if [[ -z "${UPGRADE_WAIT_AFTER_BOOT}" || "${UPGRADE_WAIT_AFTER_BOOT}" == "null" ]]; then
    UPGRADE_WAIT_AFTER_BOOT="30min"
fi

NOFILE_LIMITS=$(echo "${1}" | jq -r 'try .["nofile-limits"]')
if [[ -z "${NOFILE_LIMITS}" || "${NOFILE_LIMITS}" == "null" ]]; then
    NOFILE_LIMITS=false
fi

BREW_ANALYTICS=$(echo "${1}" | jq -r 'try .["brew-analytics"]')
if [[ -z "${BREW_ANALYTICS}" || "${BREW_ANALYTICS}" == "null" ]]; then
    BREW_ANALYTICS=true
fi

DIRECT_PULL=$(echo "${1}" | jq -r 'try .["direct-pull"]')
if [[ -z "${DIRECT_PULL}" || "${DIRECT_PULL}" == "null" ]]; then
    DIRECT_PULL=false
fi

INSTALLER_COMMIT=$(echo "${1}" | jq -r 'try .["installer-commit"]')
if [[ -z "${INSTALLER_COMMIT}" || "${INSTALLER_COMMIT}" == "null" ]]; then
    INSTALLER_COMMIT="HEAD"
fi

if [[ "${DIRECT_PULL}" == true ]]; then
    echo "Downloading Brew from homebrew..."
    curl -fLsS --retry 5 --create-dirs "https://raw.githubusercontent.com/Homebrew/install/${INSTALLER_COMMIT}/install.sh" -o /tmp/brew-install
    echo "Downloaded Brew install script"
    mkdir -p /var/home
    mkdir -p /var/roothome
    chmod +x /tmp/brew-install
    touch /.dockerenv
    env --ignore-environment PATH=/usr/bin:/bin:/usr/sbin:/sbin HOME=/home/linuxbrew NONINTERACTIVE=1 /usr/bin/bash /tmp/brew-install
    rm /.dockerenv

    # pack homebrew
    tar --zstd -cvf /tmp/homebrew-tarball.tar.zst /home/linuxbrew/.linuxbrew
    rm -rf /home/linuxbrew/.linuxbrew
else
    # Download pre-packaged Brew from uBlue repo
    asset_urls=$(curl -fLsS --retry 5 'https://api.github.com/repos/ublue-os/packages/releases' \
        | jq -cr '.[0].assets | map({(.name): .browser_download_url}) | add')
    brew_tarball_url=$(jq -cr '."homebrew-x86_64.tar.zst"' <<< "${asset_urls}")
    brew_sha256_url=$(jq -cr '."homebrew-x86_64.sha256"' <<< "${asset_urls}")

    echo "Downloading Brew tarball..."
    curl -fLsS --retry 5 --create-dirs \
        -o '/tmp/homebrew-tarball.tar.zst' "${brew_tarball_url}" \
        -o '/tmp/homebrew-tarball.sha256' "${brew_sha256_url}"
    echo "Downloaded Brew tarball."

    echo "Verifying Brew tarball checksum..."
    expected=$(sed 's/ .*//' '/tmp/homebrew-tarball.sha256')
    actual=$(sha256sum '/tmp/homebrew-tarball.tar.zst' | sed 's/ .*//')
    [[ "${expected}" == "${actual}" ]]
    echo "Checksum verified."
fi

# Extract Brew tarball to /usr/share/homebrew/ and set ownership to default user (UID 1000)
echo "Extracting Brew tarball to '/usr/share/homebrew/'"
mkdir -p "/usr/share/homebrew/"
tar -I zstd --preserve-permissions -xf "/tmp/homebrew-tarball.tar.zst" -C "/usr/share/homebrew/"
echo "Setting '/usr/share/homebrew/' permissions to UID/GID 1000"
chown -R 1000:1000 "/usr/share/homebrew/"

# Write systemd service files dynamically
echo "Writing brew-setup service"
cat >/usr/lib/systemd/system/brew-setup.service <<EOF
[Unit]
Description=Setup Brew
Wants=network-online.target
After=network-online.target
ConditionPathExists=!/etc/.linuxbrew
ConditionPathExists=!/var/home/linuxbrew/.linuxbrew

[Service]
Type=oneshot
ExecStart=/usr/bin/cp -R --update=none /usr/share/homebrew/home/linuxbrew/.linuxbrew /var/home/linuxbrew
ExecStart=/usr/bin/chown -R 1000:1000 /var/home/linuxbrew
ExecStart=/usr/bin/touch /etc/.linuxbrew

[Install]
WantedBy=default.target multi-user.target
EOF

echo "Writing brew-update service"
cat >/usr/lib/systemd/system/brew-update.service <<EOF
[Unit]
Description=Auto-update Brew binary
After=local-fs.target
After=network-online.target
ConditionPathIsSymbolicLink=/home/linuxbrew/.linuxbrew/bin/brew

[Service]
User=1000
Type=oneshot
Environment=HOMEBREW_CELLAR=/home/linuxbrew/.linuxbrew/Cellar
Environment=HOMEBREW_PREFIX=/home/linuxbrew/.linuxbrew
Environment=HOMEBREW_REPOSITORY=/home/linuxbrew/.linuxbrew/Homebrew
ExecStart=/usr/bin/bash -c "/home/linuxbrew/.linuxbrew/bin/brew update"
EOF

echo "Writing brew-upgrade service"
cat >/usr/lib/systemd/system/brew-upgrade.service <<EOF
[Unit]
Description=Auto-upgrade Brew packages
After=local-fs.target
After=network-online.target
ConditionPathIsSymbolicLink=/home/linuxbrew/.linuxbrew/bin/brew

[Service]
User=1000
Type=oneshot
Environment=HOMEBREW_CELLAR=/home/linuxbrew/.linuxbrew/Cellar
Environment=HOMEBREW_PREFIX=/home/linuxbrew/.linuxbrew
Environment=HOMEBREW_REPOSITORY=/home/linuxbrew/.linuxbrew/Homebrew
ExecStart=/usr/bin/bash -c "/home/linuxbrew/.linuxbrew/bin/brew upgrade"
ExecStartPost=-/usr/bin/bash -c "/home/linuxbrew/.linuxbrew/bin/brew unlink systemd"
ExecStartPost=-/usr/bin/bash -c "/home/linuxbrew/.linuxbrew/bin/brew unlink dbus"
ExecStartPost=-/usr/bin/bash -c "/home/linuxbrew/.linuxbrew/bin/brew unlink gsettings"
ExecStartPost=-/usr/bin/bash -c "/home/linuxbrew/.linuxbrew/bin/brew unlink bash"
ExecStartPost=-/usr/bin/bash -c "/home/linuxbrew/.linuxbrew/bin/brew unlink rpm"
EOF

# Write systemd timer files dynamically
echo "Writing brew-update timer"
if [[ -n "${UPDATE_WAIT_AFTER_BOOT}" ]] && [[ "${UPDATE_WAIT_AFTER_BOOT}" != "10min" ]]; then
  echo "Applying custom 'wait-after-boot' value in '${UPDATE_WAIT_AFTER_BOOT}' time interval for brew update timer"
fi
if [[ -n "${UPDATE_INTERVAL}" ]] && [[ "${UPDATE_INTERVAL}" != "6h" ]]; then
  echo "Applying custom 'update-interval' value in '${UPDATE_INTERVAL}' time interval for brew update timer"
fi
cat >/usr/lib/systemd/system/brew-update.timer <<EOF
[Unit]
Description=Timer for updating Brew binary
Wants=network-online.target

[Timer]
OnBootSec=${UPDATE_WAIT_AFTER_BOOT}
OnUnitInactiveSec=${UPDATE_INTERVAL}
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "Writing brew-upgrade timer"
if [[ -n "${UPGRADE_WAIT_AFTER_BOOT}" ]] && [[ "${UPGRADE_WAIT_AFTER_BOOT}" != "30min" ]]; then
  echo "Applying custom 'wait-after-boot' value in '${UPGRADE_WAIT_AFTER_BOOT}' time interval for brew upgrade timer"
fi
if [[ -n "${UPGRADE_INTERVAL}" ]] && [[ "${UPGRADE_INTERVAL}" != "8h" ]]; then
  echo "Applying custom 'upgrade-interval' value in '${UPGRADE_INTERVAL}' time interval for brew upgrade timer"
fi
cat >/usr/lib/systemd/system/brew-upgrade.timer <<EOF
[Unit]
Description=Timer for upgrading Brew packages
Wants=network-online.target

[Timer]
OnBootSec=${UPGRADE_WAIT_AFTER_BOOT}
OnUnitInactiveSec=${UPGRADE_INTERVAL}
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Apply brew shell environment only when shell is interactive
# Fish already includes this fix in brew-fish-completions.sh
# By default Brew applies the shell environment changes globally, which causes path conflicts between system & brew installed programs with same name.
# Universal Blue images include this same fix
if [[ ! -d "/etc/profile.d/" ]]; then
  mkdir -p "/etc/profile.d/"
fi
if [[ ! -f "/etc/profile.d/brew.sh" ]]; then
  echo "Apply brew path export fix, to solve path conflicts between system & brew programs with same name"
  cat > /etc/profile.d/brew.sh <<EOF
#!/usr/bin/env bash
if [[ -d /home/linuxbrew/.linuxbrew && \$- == *i* && "\$(/usr/bin/id -u)" != 0 ]]; then
  eval "\$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
fi
EOF
fi

# Copy shell configuration files
echo "Copying Brew bash & fish shell completions"
cp -r "${MODULE_DIRECTORY}"/brew/brew-fish-completions.fish /usr/share/fish/vendor_conf.d/brew-fish-completions.fish
cp -r "${MODULE_DIRECTORY}"/brew/brew-bash-completions.sh /etc/profile.d/brew-bash-completions.sh

# Register path symlink
# We do this via tmpfiles.d so that it is created by the live system.
echo "Writing brew tmpfiles.d configuration"
cat >/usr/lib/tmpfiles.d/homebrew.conf <<EOF
d /var/lib/homebrew 0755 1000 1000 - -
d /var/cache/homebrew 0755 1000 1000 - -
d /var/home/linuxbrew 0755 1000 1000 - -
EOF

# Ensure systemd preset directory exists
mkdir -p /usr/lib/systemd/system-preset
SERVICE_PRESET_FILE='/usr/lib/systemd/system-preset/20-brew.preset'

# Enable the setup service
echo "Enabling brew-setup service to install Brew in run-time"
echo 'enable brew-setup.service' >> "$SERVICE_PRESET_FILE"

# Always enable or disable update and upgrade services for consistency
if [[ "${AUTO_UPDATE}" == true ]]; then
    echo "Enabling auto-updates for Brew binary"
    echo 'enable brew-update.timer' >> "$SERVICE_PRESET_FILE"
else
    echo "Disabling auto-updates for Brew binary"
    echo 'disable brew-update.timer' >> "$SERVICE_PRESET_FILE"
fi

if [[ "${AUTO_UPGRADE}" == true ]]; then
    echo "Enabling auto-upgrades for Brew packages"
    echo 'enable brew-upgrade.timer' >> "$SERVICE_PRESET_FILE"
else
    echo "Disabling auto-upgrades for Brew packages"
    echo 'disable brew-upgrade.timer' >> "$SERVICE_PRESET_FILE"
fi

# Apply presets defined above
systemctl preset brew-setup.service brew-update.timer brew-upgrade.timer

# Apply nofile limits if enabled
if [[ "${NOFILE_LIMITS}" == true ]]; then
  source "${MODULE_DIRECTORY}/brew/brew-nofile-limits-logic.sh"
fi

# Disable homebrew analytics if the flag is set to false
# like secureblue: https://github.com/secureblue/secureblue/blob/live/config/scripts/homebrewanalyticsoptout.sh
if [[ "${BREW_ANALYTICS}" == false ]]; then
  if [[ ! -f "/etc/environment" ]]; then
    echo "" > "/etc/environment" # touch fails for some reason, probably a bug with it
  fi
  CURRENT_ENVIRONMENT=$(cat "/etc/environment")
  CURRENT_HOMEBREW_CONFIG=$(awk -F= '/HOMEBREW_NO_ANALYTICS/ {print $0}' "/etc/environment")
  if [[ -n "${CURRENT_ENVIRONMENT}" ]]; then
    if [[ "${CURRENT_HOMEBREW_CONFIG}" == "HOMEBREW_NO_ANALYTICS=0" ]]; then
      echo "Disabling Brew analytics"
      sed -i 's/HOMEBREW_NO_ANALYTICS=0/HOMEBREW_NO_ANALYTICS=1/' "/etc/environment"
    elif [[ -z "${CURRENT_HOMEBREW_CONFIG}" ]]; then
      echo "Disabling Brew analytics"
      echo "HOMEBREW_NO_ANALYTICS=1" >> "/etc/environment"
    elif [[ "${CURRENT_HOMEBREW_CONFIG}" == "HOMEBREW_NO_ANALYTICS=1" ]]; then
      echo "Brew analytics are already disabled!"
    fi
  elif [[ -z "${CURRENT_ENVIRONMENT}" ]]; then
    echo "Disabling Brew analytics"
    echo "HOMEBREW_NO_ANALYTICS=1" > "/etc/environment"
  fi
fi

echo "Brew setup completed"
