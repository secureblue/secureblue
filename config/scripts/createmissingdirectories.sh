
#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# https://bugzilla.redhat.com/show_bug.cgi?id=2259249
mkdir /var/log/usbguard

mkdir /var/lib/setroubleshoot
chown setroubleshoot:setroubleshoot /var/lib/setroubleshoot
chmod 600 /var/lib/setroubleshoot
