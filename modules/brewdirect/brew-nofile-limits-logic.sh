#!/usr/bin/env bash

set -euo pipefail

# Script used to read nofile limits from the base image, since issuing easy systemctl status commands don't work in build-time.
# Takes into account config priorities & current config settings regarding nofile limits
# (if nofile limit is already applied with appropriate values in the base image, than this tweak is not applied)
# Modifies limits nofile value & systemd DefaultLimitNOFILE value

DESIRED_SOFT_LIMIT=4096
DESIRED_HARD_LIMIT=524288
BREW_LIMITS_D_CONFIG="/etc/security/limits.d/zz1-brew-limits.conf"
BREW_SYSTEMD_SYSTEM_CONFIG="/usr/lib/systemd/system.conf.d/zz1-brew-limits.conf"
BREW_SYSTEMD_USER_CONFIG="/usr/lib/systemd/user.conf.d/zz1-brew-limits.conf"

# SSH/TTY nofile limit (security ulimit config)

# From least to most preferred
SSH_TTY_LIMIT_ORDER=(
"/etc/security/limits.conf"
"/etc/security/limits.d/"
)
updated_ssh_array=()
for path in "${SSH_TTY_LIMIT_ORDER[@]}"; do
    if [ -e "${path}" ]; then
        updated_ssh_array+=("${path}")
    fi
done
# Update the original array with the existing paths
SSH_TTY_LIMIT_ORDER=("${updated_ssh_array[@]}")

# Soft SSH/TTY nofile limit
SSH_TTY_SOFT_INFO=$(find "${SSH_TTY_LIMIT_ORDER[@]}" -type f -name "*.conf" -exec awk -v OFS='\t' '/soft\s+nofile/ && !/^#/ {sub(/.*nofile/, ""); gsub(/^[ \t]+/, ""); print FILENAME, $0}' {} + | tail -n 1)
if [[ -n "${SSH_TTY_SOFT_INFO}" ]]; then
  CURRENT_SSH_TTY_SOFT_VALUE=$(echo "${SSH_TTY_SOFT_INFO}" | awk '{print $2}')
else
  CURRENT_SSH_TTY_SOFT_VALUE=0
fi

# Hard SSH/TTY nofile limit
SSH_TTY_HARD_INFO=$(find "${SSH_TTY_LIMIT_ORDER[@]}" -type f -name "*.conf" -exec awk -v OFS='\t' '/hard\s+nofile/ && !/^#/ {sub(/.*nofile/, ""); gsub(/^[ \t]+/, ""); print FILENAME, $0}' {} + | tail -n 1)
if [[ -n "${SSH_TTY_HARD_INFO}" ]]; then
  CURRENT_SSH_TTY_HARD_VALUE=$(echo "${SSH_TTY_HARD_INFO}" | awk '{print $2}')
else
  CURRENT_SSH_TTY_HARD_VALUE=0
fi

# SystemD nofile limit

# SystemD system soft & hard nofile limit
# From least to most preferred
SYSTEMD_SYSTEM_LIMIT_ORDER=(
"/usr/lib/systemd/system.conf"
"/usr/lib/systemd/system.conf.d/"
"/etc/systemd/system.conf"
"/etc/systemd/system.conf.d/"
)
updated_systemd_system_array=()
for path in "${SYSTEMD_SYSTEM_LIMIT_ORDER[@]}"; do
    if [ -e "${path}" ]; then
        updated_systemd_system_array+=("${path}")
    fi
done
# Update the original array with the existing paths
SYSTEMD_SYSTEM_LIMIT_ORDER=("${updated_systemd_system_array[@]}")

# SystemD system soft & hard nofile limit
SYSTEMD_SYSTEM_SOFT_INFO=$(find "${SYSTEMD_SYSTEM_LIMIT_ORDER[@]}" -type f -name "*.conf" -exec awk -F'[:=]' '/^[^#]*DefaultLimitNOFILE/ {print FILENAME, $2}' {} + | tail -n 1)
if [[ -n "${SYSTEMD_SYSTEM_SOFT_INFO}" ]]; then
  CURRENT_SYSTEMD_SYSTEM_SOFT_VALUE=$(echo "${SYSTEMD_SYSTEM_SOFT_INFO}" | awk '{print $2}')
else
  CURRENT_SYSTEMD_SYSTEM_SOFT_VALUE=0
fi

SYSTEMD_SYSTEM_HARD_INFO=$(find "${SYSTEMD_SYSTEM_LIMIT_ORDER[@]}" -type f -name "*.conf" -exec awk -F'[:=]' '/^[^#]*DefaultLimitNOFILE/ {print FILENAME, $3}' {} + | tail -n 1)
if [[ -n "${SYSTEMD_SYSTEM_HARD_INFO}" ]]; then
  CURRENT_SYSTEMD_SYSTEM_HARD_VALUE=$(echo "${SYSTEMD_SYSTEM_HARD_INFO}" | awk '{print $2}')
else
  CURRENT_SYSTEMD_SYSTEM_HARD_VALUE=0
fi

# SystemD user soft & hard nofile limit
SYSTEMD_USER_LIMIT_ORDER=(
"/usr/lib/systemd/user.conf"
"/usr/lib/systemd/user.conf.d/"
"/etc/systemd/user.conf"
"/etc/systemd/user.conf.d/"
)
updated_systemd_user_array=()
for path in "${SYSTEMD_USER_LIMIT_ORDER[@]}"; do
    if [ -e "${path}" ]; then
        updated_systemd_user_array+=("${path}")
    fi
done
# Update the original array with the existing paths
SYSTEMD_USER_LIMIT_ORDER=("${updated_systemd_user_array[@]}")

SYSTEMD_USER_SOFT_INFO=$(find "${SYSTEMD_USER_LIMIT_ORDER[@]}" -type f -name "*.conf" -exec awk -F'[:=]' '/^[^#]*DefaultLimitNOFILE/ {print FILENAME, $2}' {} + | tail -n 1)
if [[ -n "${SYSTEMD_USER_SOFT_INFO}" ]]; then
  CURRENT_SYSTEMD_USER_SOFT_VALUE=$(echo "${SYSTEMD_USER_SOFT_INFO}" | awk '{print $2}')
else
  CURRENT_SYSTEMD_USER_SOFT_VALUE=0
fi

SYSTEMD_USER_HARD_INFO=$(find "${SYSTEMD_USER_LIMIT_ORDER[@]}" -type f -name "*.conf" -exec awk -F'[:=]' '/^[^#]*DefaultLimitNOFILE/ {print FILENAME, $3}' {} + | tail -n 1)
if [[ -n "${SYSTEMD_USER_HARD_INFO}" ]]; then
  CURRENT_SYSTEMD_USER_HARD_VALUE=$(echo "${SYSTEMD_USER_HARD_INFO}" | awk '{print $2}')
else
  CURRENT_SYSTEMD_USER_HARD_VALUE=0
fi

# Check current state

echo "Current nofile limit values:"
check_and_print() {
    if [[ "${1}" -eq 0 ]]; then
        echo "UNSET"
    else
        echo "${1}"
    fi
}
echo "SSH/TTY soft nofile limit: $(check_and_print "${CURRENT_SSH_TTY_SOFT_VALUE}")"
echo "SSH/TTY hard nofile limit: $(check_and_print "${CURRENT_SSH_TTY_HARD_VALUE}")"
echo "SystemD system soft nofile limit: $(check_and_print "${CURRENT_SYSTEMD_SYSTEM_SOFT_VALUE}")"
echo "SystemD system hard nofile limit: $(check_and_print "${CURRENT_SYSTEMD_SYSTEM_HARD_VALUE}")"
echo "SystemD user soft nofile limit: $(check_and_print "${CURRENT_SYSTEMD_USER_SOFT_VALUE}")"
echo "SystemD user hard nofile limit: $(check_and_print "${CURRENT_SYSTEMD_USER_HARD_VALUE}")"

# Write nofile limit values
# zz1- prefix is used for config, to assure that nofile limit is going to be applied, as it's high in lexical order.
# If config is higher in lexical order, that means that it's preferred over other ones.
# Downstreams can just go on with their own modifications in zz2-, zz3-, zz4-, zz5-, etc. increments
# if they wish to experiment with nofile limits differently

# Write SSH/TTY nolimit values
if [[ "${CURRENT_SSH_TTY_SOFT_VALUE}" -lt "${DESIRED_SOFT_LIMIT}" ]] || [[ "${CURRENT_SSH_TTY_HARD_VALUE}" -lt "${DESIRED_HARD_LIMIT}" ]]; then
  if [[ ! -d "/etc/security/limits.d/" ]]; then
    mkdir -p "/etc/security/limits.d/"
  fi
  echo "# This file sets the resource limits for users logged in via PAM,
# more specifically, users logged in via SSH or tty (console).
# Limits related to terminals in Wayland/Xorg sessions depend on a
# change to /etc/systemd/user.conf.
# This does not affect resource limits of the system services.
# This file overrides defaults set in /etc/security/limits.conf

" > "${BREW_LIMITS_D_CONFIG}"
fi

if [[ "${CURRENT_SSH_TTY_SOFT_VALUE}" -lt "${DESIRED_SOFT_LIMIT}" ]] && [[ "${CURRENT_SSH_TTY_HARD_VALUE}" -ge "${DESIRED_HARD_LIMIT}" ]]; then
  echo "Writing increased SSH/TTY soft nofile limit value"
  echo "* soft nofile ${DESIRED_SOFT_LIMIT}" >> "${BREW_LIMITS_D_CONFIG}"
elif [[ "${CURRENT_SSH_TTY_SOFT_VALUE}" -ge "${DESIRED_SOFT_LIMIT}" ]]; then
  echo "Required SSH/TTY soft nofile limit value is already satisfied!"
fi

if [[ "${CURRENT_SSH_TTY_SOFT_VALUE}" -ge "${DESIRED_SOFT_LIMIT}" ]] && [[ "${CURRENT_SSH_TTY_HARD_VALUE}" -lt "${DESIRED_HARD_LIMIT}" ]]; then
  echo "Writing increased SSH/TTY hard nofile limit value"
  echo "* hard nofile ${DESIRED_HARD_LIMIT}" >> "${BREW_LIMITS_D_CONFIG}"
elif [[ "${CURRENT_SSH_TTY_HARD_VALUE}" -ge "${DESIRED_HARD_LIMIT}" ]]; then
  echo "Required SSH/TTY hard nofile limit value is already satisfied!"
fi

if [[ "${CURRENT_SSH_TTY_SOFT_VALUE}" -ge "${DESIRED_SOFT_LIMIT}" ]] && [[ "${CURRENT_SSH_TTY_HARD_VALUE}" -lt "${DESIRED_HARD_LIMIT}" ]]; then
  echo "Writing increased SSH/TTY soft & hard nofile limit value"
  echo "* soft nofile ${DESIRED_SOFT_LIMIT}" >> "${BREW_LIMITS_D_CONFIG}"
  echo "* hard nofile ${DESIRED_HARD_LIMIT}" >> "${BREW_LIMITS_D_CONFIG}"
fi

# Write SystemD nolimit values

# Writing SystemD system nolimit values
if [[ "${CURRENT_SYSTEMD_SYSTEM_SOFT_VALUE}" -lt "${DESIRED_SOFT_LIMIT}" ]] || [[ "${CURRENT_SYSTEMD_SYSTEM_HARD_VALUE}" -lt "${DESIRED_HARD_LIMIT}" ]]; then
  if [[ ! -d "/usr/lib/systemd/system.conf.d/" ]]; then
    mkdir -p "/usr/lib/systemd/system.conf.d/"
  fi
fi

if [[ "${CURRENT_SYSTEMD_SYSTEM_SOFT_VALUE}" -lt "${DESIRED_SOFT_LIMIT}" ]] && [[ "${CURRENT_SYSTEMD_SYSTEM_HARD_VALUE}" -ge "${DESIRED_HARD_LIMIT}" ]]; then
  echo "Writing increased SystemD system soft nofile limit value"
  echo "[Manager]
DefaultLimitNOFILE=${DESIRED_SOFT_LIMIT}:${CURRENT_SYSTEMD_SYSTEM_HARD_VALUE}" > "${BREW_SYSTEMD_SYSTEM_CONFIG}"
elif [[ "${CURRENT_SYSTEMD_SYSTEM_SOFT_VALUE}" -ge "${DESIRED_SOFT_LIMIT}" ]]; then
  echo "Required SystemD system soft nofile limit value is already satisfied!"
fi

if [[ "${CURRENT_SYSTEMD_SYSTEM_SOFT_VALUE}" -ge "${DESIRED_SOFT_LIMIT}" ]] && [[ "${CURRENT_SYSTEMD_SYSTEM_HARD_VALUE}" -lt "${DESIRED_HARD_LIMIT}" ]]; then
  echo "Writing increased SystemD system hard nofile limit value"
  echo "[Manager]
DefaultLimitNOFILE=${CURRENT_SYSTEMD_SYSTEM_SOFT_VALUE}:${DESIRED_HARD_LIMIT}" > "${BREW_SYSTEMD_SYSTEM_CONFIG}"
elif [[ "${CURRENT_SYSTEMD_SYSTEM_HARD_VALUE}" -ge "${DESIRED_HARD_LIMIT}" ]]; then
  echo "Required SystemD system hard nofile limit value is already satisfied!"
fi

if [[ "${CURRENT_SYSTEMD_SYSTEM_SOFT_VALUE}" -lt "${DESIRED_SOFT_LIMIT}" ]] && [[ "${CURRENT_SYSTEMD_SYSTEM_HARD_VALUE}" -lt "${DESIRED_HARD_LIMIT}" ]]; then
  echo "Writing increased SystemD system soft & hard nofile limit value"
  echo "[Manager]
DefaultLimitNOFILE=${DESIRED_SOFT_LIMIT}:${DESIRED_HARD_LIMIT}" > "${BREW_SYSTEMD_SYSTEM_CONFIG}"
fi

# Writing SystemD user nolimit values
if [[ "${CURRENT_SYSTEMD_USER_SOFT_VALUE}" -lt "${DESIRED_SOFT_LIMIT}" ]] || [[ "${CURRENT_SYSTEMD_USER_HARD_VALUE}" -lt "${DESIRED_HARD_LIMIT}" ]]; then
  if [[ ! -d "/usr/lib/systemd/user.conf.d/" ]]; then
    mkdir -p "/usr/lib/systemd/user.conf.d/"
  fi
fi

if [[ "${CURRENT_SYSTEMD_USER_SOFT_VALUE}" -lt "${DESIRED_SOFT_LIMIT}" ]] && [[ "${CURRENT_SYSTEMD_USER_HARD_VALUE}" -ge "${DESIRED_HARD_LIMIT}" ]]; then
  echo "Writing increased SystemD user soft nofile limit value"
  echo "[Manager]
DefaultLimitNOFILE=${DESIRED_SOFT_LIMIT}:${CURRENT_SYSTEMD_USER_HARD_VALUE}" > "${BREW_SYSTEMD_USER_CONFIG}"
elif [[ "${CURRENT_SYSTEMD_USER_SOFT_VALUE}" -ge "${DESIRED_SOFT_LIMIT}" ]]; then
  echo "Required SystemD user soft nofile limit value is already satisfied!"
fi

if [[ "${CURRENT_SYSTEMD_USER_SOFT_VALUE}" -ge "${DESIRED_SOFT_LIMIT}" ]] && [[ "${CURRENT_SYSTEMD_USER_HARD_VALUE}" -lt "${DESIRED_HARD_LIMIT}" ]]; then
  echo "Writing increased SystemD user hard nofile limit value"
  echo "[Manager]
DefaultLimitNOFILE=${CURRENT_SYSTEMD_USER_SOFT_VALUE}:${DESIRED_HARD_LIMIT}" > "${BREW_SYSTEMD_USER_CONFIG}"
elif [[ "${CURRENT_SYSTEMD_USER_HARD_VALUE}" -ge "${DESIRED_HARD_LIMIT}" ]]; then
  echo "Required SystemD user hard nofile limit value is already satisfied!"
fi

if [[ "${CURRENT_SYSTEMD_USER_SOFT_VALUE}" -lt "${DESIRED_SOFT_LIMIT}" ]] && [[ "${CURRENT_SYSTEMD_USER_HARD_VALUE}" -lt "${DESIRED_HARD_LIMIT}" ]]; then
  echo "Writing increased SystemD user soft & hard nofile limit value"
  echo "[Manager]
DefaultLimitNOFILE=${DESIRED_SOFT_LIMIT}:${DESIRED_HARD_LIMIT}" > "${BREW_SYSTEMD_USER_CONFIG}"
fi
