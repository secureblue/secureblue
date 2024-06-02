#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i 's/FEATURES=""/FEATURES="SplitCacheByNetworkIsolationKey,SplitCodeCacheByNetworkIsolationKey,SplitHostCacheByNetworkIsolationKey,PrefetchPrivacyChanges,IsolateSandboxedIframes,StrictOriginIsolation,PartitionConnectionsByNetworkIsolationKey,PartitionHttpServerPropertiesByNetworkIsolationKey,PartitionSSLSessionsByNetworkIsolationKey,PartitionNelAndReportingByNetworkIsolationKey,EnableCrossSiteFlagNetworkIsolationKey,"/g' /etc/chromium/chromium.conf

# Not temporary, keep:
echo '

CHROMIUM_FLAGS+=" --ozone-platform=wayland --no-pings --disk-cache-dir=/dev/null --disable-features=PrivacySandboxSettings4,InterestFeedV2,NTPPopularSitesBakedInContent,UsePopularSitesSuggestions,MediaDrmPreprovisioning,AutofillServerCommunication,DisableThirdPartyStoragePartitioningDeprecationTrial"

' >> /etc/chromium/chromium.conf
