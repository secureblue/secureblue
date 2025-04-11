#!/usr/bin/env bash

set -oue pipefail

systemctl enable securebluefirstrun.service
systemctl enable securebluecleanup.service