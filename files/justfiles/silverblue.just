# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Toggle Gnome JIT JavaScript for GJS and WebkitGTK (requires session restart).
[positional-arguments]
@set-gnome-jit-js *args:
    exec /usr/bin/python3 /usr/libexec/secureblue/set_gnome_jit_js.py "$@"

# Toggle support for using GNOME user extensions
toggle-gnome-extensions:
    #!/usr/bin/bash
    GSETTING="$(/usr/bin/gsettings get org.gnome.shell allow-extension-installation)"
    if [[ "${GSETTING}" == "false" ]]; then
        /usr/bin/gsettings set org.gnome.shell allow-extension-installation true
        echo "Support for GNOME user extensions have been enabled"
    else
        /usr/bin/gsettings reset org.gnome.shell allow-extension-installation
        echo "Support for GNOME user extensions have been disabled"
    fi
