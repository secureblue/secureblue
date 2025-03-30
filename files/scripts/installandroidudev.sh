#!/usr/bin/env bash

set -oue pipefail

LATEST_ANDROID_UDEV_RULES_COMMIT="e23e31266740b0dc550d636c68b6724620c0299e" # 20250314
curl -OL "https://github.com/M0Rf30/android-udev-rules/archive/${LATEST_ANDROID_UDEV_RULES_COMMIT}.tar.gz"
tar xvf "${LATEST_ANDROID_UDEV_RULES_COMMIT}.tar.gz" --strip-components=1

install -m 644 51-android.rules /etc/udev/rules.d/
mkdir -p /usr/lib/sysusers.d/
install -m 644 android-udev.conf /usr/lib/sysusers.d/.