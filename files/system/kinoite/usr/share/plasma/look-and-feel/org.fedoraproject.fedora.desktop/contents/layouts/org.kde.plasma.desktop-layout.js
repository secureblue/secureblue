/*
 * SPDX-FileCopyrightText: Copyright Fedora Project Authors.
 * SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
 *
 * SPDX-License-Identifier: MIT
 */

loadTemplate("org.kde.plasma.desktop.defaultPanel");

const desktopsArray = desktopsForActivity(currentActivity());
desktopsArray.forEach(desktop => {
    desktop.wallpaperPlugin = 'org.kde.image';
    desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desktop.writeConfig("Image", "file:///usr/share/backgrounds/default.png");
});
