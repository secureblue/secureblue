#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i 's/<forward/>/<service name="ssh"/>\n<forward/>/' /usr/etc/firewalld/zones/FedoraWorkstation.xml








