
#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i '/squashfs/d' /usr/etc/modprobe.d/blacklist.conf