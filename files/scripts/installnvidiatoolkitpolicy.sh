#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

semodule --verbose --install /usr/share/selinux/packages/nvidia-container.pp