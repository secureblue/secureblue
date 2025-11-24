#!/usr/bin/env bash

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

# Copyright (c) 2022 Fedora Sway SIG
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
