#!/usr/bin/env bash

# Tell this script to exit if there are any errors.
# You should have this in every custom script, to ensure that your completed
# builds actually ran successfully without any errors!
set -oue pipefail

# add our just config
echo 'import "/usr/share/ublue-os/just/70-secureblue.just"' >> /usr/share/ublue-os/justfile
