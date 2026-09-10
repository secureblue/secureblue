#!/bin/bash

# Enable zswap with preferred parameters
enable_zswap() {
    echo 1 > /sys/module/zswap/parameters/enabled
    echo zstd > /sys/module/zswap/parameters/compressor
}

case "$1" in
    start)
        enable_zswap
        ;;
    stop)
        swapoff -a
        echo 0 > /sys/module/zswap/parameters/enabled
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac

exit 0
