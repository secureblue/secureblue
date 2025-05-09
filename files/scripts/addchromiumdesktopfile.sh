#!/usr/bin/env bash

set -oue pipefail

sed -i 's/org.mozilla.firefox/trivalent/' /usr/share/wayfire/wf-shell.ini 
