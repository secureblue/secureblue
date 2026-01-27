#!/usr/bin/env bash

set -euo pipefail

PORTALS_CONF="/usr/share/xdg-desktop-portal/sway-portals.conf"

sed -Ei '/^org\.freedesktop\.impl\.portal\.Screen(Cast|shot)=wlr$/s/=wlr/=none/' "$PORTALS_CONF"
