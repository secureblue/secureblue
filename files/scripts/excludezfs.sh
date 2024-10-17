#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo '

omit_dracutmodules+=" zfs "

' > /usr/lib/dracut/dracut.conf.d/99-omit-zfs.conf
