#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i 's/libhardened_malloc.so/libhardened_malloc-light.so/' /etc/ld.so.preload
