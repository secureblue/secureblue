#!/usr/bin/env bash

set -oue pipefail

sed -i 's/libhardened_malloc.so/libhardened_malloc-light.so/' /etc/ld.so.preload
