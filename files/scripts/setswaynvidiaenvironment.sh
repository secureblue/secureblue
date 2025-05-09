#!/usr/bin/env bash

set -oue pipefail

rm /etc/sway/environment

# shellcheck disable=SC2016
echo '

# This file is a part of Fedora configuration for Sway and will be sourced
# from /usr/bin/start-sway script for all users of the system.
# User-specific variables should be placed in $XDG_CONFIG_HOME/sway/environment
#
# vim: set ft=sh:

## Pass extra arguments to the /usr/bin/sway executable

#SWAY_EXTRA_ARGS="$SWAY_EXTRA_ARGS --unsupported-gpu"
SWAY_EXTRA_ARGS="$SWAY_EXTRA_ARGS --unsupported-gpu -D noscanout"
#SWAY_EXTRA_ARGS="$SWAY_EXTRA_ARGS --debug"

## Set environment variables

# Useful variables for wlroots:
# https://gitlab.freedesktop.org/wlroots/wlroots/-/blob/master/docs/env_vars.md
WLR_NO_HARDWARE_CURSORS=1
# Setting renderer to Vulkan may fix flickering but needs the following extensions:
# - VK_EXT_image_drm_format_modifier
# - VK_EXT_physical_device_drm
#
# Source: https://gitlab.freedesktop.org/wlroots/wlroots/-/commit/8e346922508aa3eaccd6e12f2917f6574f349843
WLR_RENDERER=vulkan

# Java Application compatibility
# Source: https://github.com/swaywm/wlroots/issues/1464
_JAVA_AWT_WM_NONREPARENTING=1

' > /etc/sway/environment
