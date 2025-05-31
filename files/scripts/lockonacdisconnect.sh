#!/usr/bin/env bash
set -oue pipefail

# Locks all user sessions when AC is unplugged
loginctl lock-sessions