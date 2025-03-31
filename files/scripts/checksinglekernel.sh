#!/usr/bin/env bash

set -oue pipefail

KERNEL_COUNT=$(find /usr/lib/modules -mindepth 1 -maxdepth 1 -type d | wc -l)
if [ "$KERNEL_COUNT" -ne 1 ]; then
    echo "Expected single kernel. Found $KERNEL_COUNT kernels. Exiting..."
    exit 1
fi
