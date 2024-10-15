
#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i 's/org.mozilla.firefox/chromium-browser/' /usr/share/wayfire/wf-shell.ini 
