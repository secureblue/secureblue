

#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i 's@XDG_CONFIG_HOME=/usr/etc/ river@XDG_CONFIG_HOME=/usr/etc/ river -no-xwayland@g' /usr/bin/startriver
