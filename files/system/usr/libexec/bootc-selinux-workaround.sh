#!/usr/bin/bash
if ! [ -e /var/lib/secureblue/bootc-selinux-workaround-$(bootc status --booted --format json | jq -r '.status.booted.image.timestamp').stamp ]; then
    rm -f /var/lib/secureblue/bootc-selinux-workaround-*.stamp;
    /usr/bin/semodule -B;
    /usr/bin/restorecon -R /tmp;
    touch /var/lib/secureblue/bootc-selinux-workaround-$(bootc status --booted --format json | jq -r '.status.booted.image.timestamp').stamp;
fi
