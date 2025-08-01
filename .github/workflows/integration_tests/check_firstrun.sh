#!/usr/bin/env bash

SERVICE_NAME="securebluefirstrun.service"
if ! systemctl is-enabled --quiet "$SERVICE_NAME"; then
    echo "Error: $SERVICE_NAME is in a disabled state."
    exit 1
fi

if systemctl is-failed --quiet "$SERVICE_NAME"; then
    echo "Error: $SERVICE_NAME is in a failed state."
    exit 1
fi