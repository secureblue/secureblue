#!/usr/bin/env bash

set -oue pipefail

PORTALS_CONF="/usr/share/xdg-desktop-portal/sway-portals.conf"

sed -i "s/org\.freedesktop\.impl\.portal\.ScreenCast=wlr/org.freedesktop.impl.portal.ScreenCast=none/" "$PORTALS_CONF"
sed -i "s/org\.freedesktop\.impl\.portal\.Screenshot=wlr/org.freedesktop.impl.portal.Screenshot=none/" "$PORTALS_CONF"
