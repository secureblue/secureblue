#!/usr/bin/env bash

set -oue pipefail

find ./certs -type f -execdir shred -u '{}' +
rm -rf ./certs
