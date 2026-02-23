// SPDX-FileCopyrightText: Copyright 2026 Universal Blue
// SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
//
// SPDX-License-Identifier: Apache-2.0

// Sets default launchers in KDE Plasma taskbar.
// For documentation on this scripting mechanism, see:
// https://develop.kde.org/docs/plasma/scripting/

/* global panelIds, panelById */

panelIds.forEach((panelId) => {
    const panel = panelById(panelId);
    if (!panel) {
        return;
    }
    panel.widgetIds.forEach((widgetId) => {
        const widget = panel.widgetById(widgetId);
        if (widget.type === "org.kde.plasma.taskmanager") {
            widget.currentConfigGroup = ["General"];

            // Read the current launchers value
            const currentLaunchers = widget.readConfig("launchers", "");

            // Only set our default if launchers is empty
            if (!currentLaunchers || currentLaunchers.trim() === "") {
                widget.writeConfig("launchers", [
                    "applications:systemsettings.desktop",
                    "applications:io.github.kolunmi.Bazaar.desktop",
                    "preferred://filemanager",
                    "preferred://browser"
                ]);
                widget.reloadConfig();
            }
        }
    });
});
