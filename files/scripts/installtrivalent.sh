

ARCH="$(arch)"

# dnf4 must be used here due to https://github.com/rpm-software-management/dnf5/issues/1985
dnf4 install --repoid=secureblue --downloadonly --best --downloaddir=. -y trivalent

trivalent_rpm=$(find . -maxdepth 1 -type f -name "trivalent-*.${ARCH}.rpm")
trivalent_rpms_found=$(echo "$trivalent_rpm" | wc -l)
trivalent_rpm_sans_suffix=${trivalent_rpm#./trivalent-}
trivalent_version=${trivalent_rpm_sans_suffix%.${ARCH}.rpm}

if [ "$trivalent_rpms_found" -eq 1 ]; then
    echo "Found: $trivalent_rpm"
else
    echo "Number of trivalent rpms not one, found: ${trivalent_rpms_found}"
    exit 1
fi

provenance_file="${trivalent_rpm}.intoto.jsonl"
wget "https://github.com/secureblue/Trivalent/releases/download/${trivalent_rpm_sans_suffix}/${provenance_file}"

go install github.com/slsa-framework/slsa-verifier/v2/cli/slsa-verifier@v2.7.1
~/go/bin/slsa-verifier verify-artifact "${trivalent_rpm}" --provenance-path "${provenance_file}" --source-uri github.com/secureblue/Trivalent --source-tag live
if [ $? != 0 ]; then
  echo "SLSA verification failed, exiting..."
  exit 1
fi

go uninstall github.com/slsa-framework/slsa-verifier/v2/cli/slsa-verifier@v2.7.1

dnf5 install "${trivalent_rpm}" -y