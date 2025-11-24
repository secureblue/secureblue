# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
