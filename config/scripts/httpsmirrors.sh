#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

find /usr/etc/yum.repos.d/ -name "*.repo" -type f -exec sed -i 's/metalink?/metalink?protocol=https\&/g' {} \;
