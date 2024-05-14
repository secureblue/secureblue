#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i 's/insecureAcceptAnything/reject/' /usr/etc/containers/policy.json
