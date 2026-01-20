# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Toggle Gnome JIT JavaScript for GJS and WebkitGTK (requires session restart)
toggle-gnome-jit-js:
    #! /bin/run0 /bin/bash
    ENV_FILE="/etc/profile.d/gnome-disable-jit.sh"
    if test -e $ENV_FILE; then
        rm -f $ENV_FILE
        echo "JIT JavaScript for Gnome and WebkitGTK has been enabled."
    else
        cp /usr$ENV_FILE $ENV_FILE
        chmod 644 $ENV_FILE
        echo "JIT JavaScript for Gnome and WebkitGTK has been disabled."
    fi

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
