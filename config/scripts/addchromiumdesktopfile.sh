
#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i 's/launcher_thunar = thunar.desktop/launcher_chromium = chromium-browser.desktop\nlauncher_thunar = thunar.desktop/' /usr/share/wayfire/wf-shell.ini 
