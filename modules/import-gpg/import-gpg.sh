#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

rpm --import https://brave-browser-rpm-nightly.s3.brave.com/brave-core-nightly.asc 