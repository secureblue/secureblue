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

set -oue pipefail

ARCH="$(uname -m)"

dnf5 install python3-dnf golang -y

curl -Lo /etc/yum.repos.d/repo.secureblue.dev.secureblue.repo https://repo.secureblue.dev/secureblue.repo

# dnf4 must be used here due to https://github.com/rpm-software-management/dnf5/issues/1985
dnf4 install --repoid=secureblue --downloadonly --best --downloaddir=. -y trivalent

trivalent_rpms_found=0
for trivalent_rpm in trivalent-*."${ARCH}".rpm; do
    (( ++trivalent_rpms_found ))
done

if [ "$trivalent_rpms_found" -eq 1 ]; then
    echo "Found: ${trivalent_rpms_found}"
else
    echo "Number of trivalent rpms not one, found: ${trivalent_rpms_found}"
    exit 1
fi

trivalent_rpm_sans_prefix=${trivalent_rpm#trivalent-}
trivalent_version=${trivalent_rpm_sans_prefix%.${ARCH}.rpm}

provenance_file="${trivalent_rpm}.intoto.jsonl"
wget "https://github.com/secureblue/Trivalent/releases/download/${trivalent_version}/${provenance_file}"

go telemetry off
GOPROXY=https://proxy.golang.org,direct go install github.com/slsa-framework/slsa-verifier/v2/cli/slsa-verifier@v2.7.1
~/go/bin/slsa-verifier verify-artifact "${trivalent_rpm}" --provenance-path "${provenance_file}" --source-uri github.com/secureblue/Trivalent --source-branch live

rm -rf ~/go
dnf remove python3-dnf golang -y
dnf install "${trivalent_rpm}" -y