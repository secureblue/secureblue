#!/usr/bin/env bash

set -oue pipefail

find ./certs -execdir shred -u '{}' + 
rm -rf ./certs
