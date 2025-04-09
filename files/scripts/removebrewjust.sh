#!/usr/bin/env bash

set -oue pipefail

rm -f /usr/share/bluebuild/justfiles/brew.just
sed -i '/import "\/usr\/share\/bluebuild\/justfiles\/brew.just"/d' /usr/share/ublue-os/just/60-custom.just 
