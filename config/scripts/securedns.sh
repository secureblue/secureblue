#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# https://wiki.archlinux.org/title/systemd-resolved#DNSSEC
sed -i 's/#DNSSEC=no/DNSSEC=allow-downgrade/' /usr/etc/systemd/resolved.conf

# https://wiki.archlinux.org/title/systemd-resolved#DNS_over_TLS
sed -i 's/#DNSOverTLS=no/DNSOverTLS=opportunistic/' /usr/etc/systemd/resolved.conf
