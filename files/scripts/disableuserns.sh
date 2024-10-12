#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "

# Disables user namespaces
# DO NOT REMOVE
# https://github.com/containers/bubblewrap/security/advisories/GHSA-j2qp-rvxj-43vj
user.max_user_namespaces = 0

" >> /etc/sysctl.d/hardening.conf

mkdir -p /etc/systemd/system/upower.service.d/

echo "

[Service]
# Namespaces
PrivateUsers=no

" >> /etc/systemd/system/upower.service.d/namespaces.conf


mkdir -p /etc/systemd/system/colord.service.d/

echo "

[Service]
# Namespaces
PrivateUsers=no

" >> /etc/systemd/system/colord.service.d/namespaces.conf

chown root:root /usr/bin/bwrap
chmod u+s /usr/bin/bwrap


# https://bugzilla.redhat.com/show_bug.cgi?id=2300183

echo "


module chrome_sandbox_secureblue 1.0;

require {
	type chrome_sandbox_home_t;
	type chrome_sandbox_t;
	class file map;
}

#============= chrome_sandbox_t ==============

allow chrome_sandbox_t chrome_sandbox_home_t:file map;

" > chrome_sandbox_secureblue.te

checkmodule -M -m -o chrome_sandbox_secureblue.mod chrome_sandbox_secureblue.te
semodule_package -o chrome_sandbox_secureblue.pp -m chrome_sandbox_secureblue.mod
semodule -i chrome_sandbox_secureblue.pp

rm chrome_sandbox_secureblue.te
rm chrome_sandbox_secureblue.mod
rm chrome_sandbox_secureblue.pp
