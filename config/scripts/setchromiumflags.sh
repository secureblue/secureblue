#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i '/--enable-chrome-browser-cloud-management/d' /etc/chromium/chromium.conf

# https://bugzilla.redhat.com/show_bug.cgi?id=2293202
sed -i '/--enable-native-gpu-memory-buffers/d' /etc/chromium/chromium.conf

sed -i 's/FEATURES=""/FEATURES="SplitCacheByNetworkIsolationKey,SplitCodeCacheByNetworkIsolationKey,SplitHostCacheByNetworkIsolationKey,PrefetchPrivacyChanges,IsolateSandboxedIframes,StrictOriginIsolation,PartitionConnectionsByNetworkIsolationKey,PartitionHttpServerPropertiesByNetworkIsolationKey,PartitionSSLSessionsByNetworkIsolationKey,PartitionNelAndReportingByNetworkIsolationKey,EnableCrossSiteFlagNetworkIsolationKey,"/g' /etc/chromium/chromium.conf

echo '

CHROMIUM_FLAGS+=" --ozone-platform=wayland --no-pings --disk-cache-dir=/dev/null --extension-content-verification=enforce_strict --extensions-install-verification=enforce_strict --disable-features=PrivacySandboxSettings4,InterestFeedV2,NTPPopularSitesBakedInContent,UsePopularSitesSuggestions,MediaDrmPreprovisioning,AutofillServerCommunication,DisableThirdPartyStoragePartitioningDeprecationTrial,OptimizationHints,OptimizationHintsFetching,OptimizationHintsFetchingAnonymousDataConsent"

' >> /etc/chromium/chromium.conf
