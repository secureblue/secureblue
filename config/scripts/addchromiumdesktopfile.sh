
#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed 's/launcher_thunar = thunar.desktop/launcher_thunar = thunar.desktop\nlauncher_chromium = chromium-browser.desktop/' /usr/share/wayfire/wf-shell.ini 