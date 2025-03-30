#!/usr/bin/env bash

set -oue pipefail

sed -i 's@DefaultZone=public@DefaultZone=FedoraServer@g' /etc/firewalld/firewalld.conf
