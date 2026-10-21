/*
 * SPDX-FileCopyrightText: Copyright Fedora Project Authors.
 * SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
 *
 * SPDX-License-Identifier: MIT
 */

/* global loadTemplate, desktopsForActivity, currentActivity, panels */

loadTemplate("org.kde.plasma.desktop.defaultPanel");

const desktopsArray = desktopsForActivity(currentActivity());
desktopsArray.forEach((desktop) => {
    desktop.wallpaperPlugin = "org.kde.image";
    desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desktop.writeConfig("Image", "file:///usr/share/backgrounds/default.png");
});

// Sets default launchers in KDE Plasma taskbar.
// For documentation on this scripting mechanism, see:
// https://develop.kde.org/docs/plasma/scripting/

panels().forEach((panel) => {
    panel.widgets().forEach((widget) => {
        if (
            widget.type === "org.kde.plasma.icontasks" ||
            widget.type === "org.kde.plasma.taskmanager"
        ) {
            widget.currentConfigGroup = ["General"];

            // Read the current launchers value
            const currentLaunchers = widget.readConfig("launchers", "");

            // Only set our default if launchers is empty
            if (!currentLaunchers || currentLaunchers.trim() === "") {
                widget.writeConfig("launchers", [
                    "applications:systemsettings.desktop",
                    "applications:io.github.kolunmi.Bazaar.desktop",
                    "preferred://filemanager",
                    "preferred://browser",
                ]);
                widget.reloadConfig();
            }
        }
    });
});
