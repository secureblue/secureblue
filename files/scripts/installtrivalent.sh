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

ARCH="$(arch)"

dnf5 install dnf4 -y

curl -Lo /etc/yum.repos.d/repo.secureblue.dev.secureblue.repo https://repo.secureblue.dev/secureblue.repo

# dnf4 must be used here due to https://github.com/rpm-software-management/dnf5/issues/1985
dnf4 install --repoid=secureblue --downloadonly --best --downloaddir=. -y trivalent

trivalent_rpm_search=$(find . -maxdepth 1 -type f -name "trivalent-*.${ARCH}.rpm")
trivalent_rpms_found=$(echo "$trivalent_rpm" | wc -l)

if [ "$trivalent_rpms_found" -eq 1 ]; then
    echo "Found: ${trivalent_rpms_found}"
else
    echo "Number of trivalent rpms not one, found: ${trivalent_rpms_found}"
    exit 1
fi

trivalent_rpm=${trivalent_rpm_search#./}
trivalent_rpm_sans_suffix=${trivalent_rpm#trivalent-}
trivalent_version=${trivalent_rpm_sans_suffix%.${ARCH}.rpm}

provenance_file="${trivalent_rpm}.intoto.jsonl"
wget "https://github.com/secureblue/Trivalent/releases/download/${trivalent_rpm_sans_suffix}/${provenance_file}"

go install github.com/slsa-framework/slsa-verifier/v2/cli/slsa-verifier@v2.7.1
~/go/bin/slsa-verifier verify-artifact "${trivalent_rpm}" --provenance-path "${provenance_file}" --source-uri github.com/secureblue/Trivalent --source-tag live
if [ $? != 0 ]; then
  echo "SLSA verification failed, exiting..."
  exit 1
fi

go uninstall github.com/slsa-framework/slsa-verifier/v2/cli/slsa-verifier@v2.7.1

dnf5 uninstall dnf4 -y
dnf5 install "${trivalent_rpm}" -y