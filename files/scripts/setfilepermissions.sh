#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

chmod 440 /etc/sudoers.d/timeout
