#!/usr/bin/env bash

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

SERVICE_NAME="securebluefirstrun.service"
if ! systemctl is-enabled --quiet "$SERVICE_NAME"; then
    echo "Error: $SERVICE_NAME is in a disabled state."
    exit 1
else 
    echo "$SERVICE_NAME is enabled."
fi

if systemctl is-failed --quiet "$SERVICE_NAME"; then
    echo "Error: $SERVICE_NAME is in a failed state."
    exit 1
else
    echo "$SERVICE_NAME succeeded."
fi