#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

chmod 440 /usr/etc/sudoers.d/timeout
chmod 600 /usr/etc/ssh/sshd_config