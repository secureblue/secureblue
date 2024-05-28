#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# Temporary, remove after these PRs merge:
# https://src.fedoraproject.org/rpms/chromium/pull-request/42
# https://src.fedoraproject.org/rpms/chromium/pull-request/43

echo '

# system wide chromium flags

# GRAPHIC_DRIVER=[amd|intel|nvidia|default]
GRAPHIC_DRIVER=default

# WEB_DARKMODE=[on|off]
WEB_DARKMODE=off

CHROMIUM_FLAGS=""
CHROMIUM_FLAGS+=" --enable-native-gpu-memory-buffers"
CHROMIUM_FLAGS+=" --enable-gpu-memory-buffer-video-frames"
CHROMIUM_FLAGS+=" --enable-zero-copy"
CHROMIUM_FLAGS+=" --use-gl=angle"
CHROMIUM_FLAGS+=" --ignore-gpu-blocklist --disable-gpu-driver-bug-workaround"
CHROMIUM_FLAGS+=" --enable-chrome-browser-cloud-management"

case "$GRAPHIC_DRIVER" in
   amd)
      # Need new mesa with AMD multi planes support, is not yet supported in fedora
      # see https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/26165
      CHROMIUM_FLAGS+=" --use-angle=vulkan --enable-accelerated-video-decode"
      CHROMIUM_FLAGS+=" --enable-features=Vulkan,VulkanFromANGLE,DefaultANGLEVulkan,VaapiIgnoreDriverChecks,VaapiVideoDecoder,UseMultiPlaneFormatForHardwareVideo,SplitCacheByNetworkIsolationKey,SplitCodeCacheByNetworkIsolationKey,SplitHostCacheByNetworkIsolationKey,PrefetchPrivacyChanges,IsolateSandboxedIframes,StrictOriginIsolation,PartitionConnectionsByNetworkIsolationKey,PartitionHttpServerPropertiesByNetworkIsolationKey,PartitionSSLSessionsByNetworkIsolationKey,PartitionNelAndReportingByNetworkIsolationKey,EnableCrossSiteFlagNetworkIsolationKey"
      ;;
   nvidia)
      # The NVIDIA VaAPI drivers are known to not support Chromium
      # see https://crbug.com/1492880. This feature switch is
      # provided for developers to test VaAPI drivers on NVIDIA GPUs
      CHROMIUM_FLAGS+=" --use-angle=gl"
      CHROMIUM_FLAGS+=" --enable-features=VaapiVideoDecodeLinuxGL,VaapiVideoEncoder,VaapiOnNvidiaGPUs,SplitCacheByNetworkIsolationKey,SplitCodeCacheByNetworkIsolationKey,SplitHostCacheByNetworkIsolationKey,PrefetchPrivacyChanges,IsolateSandboxedIframes,StrictOriginIsolation,PartitionConnectionsByNetworkIsolationKey,PartitionHttpServerPropertiesByNetworkIsolationKey,PartitionSSLSessionsByNetworkIsolationKey,PartitionNelAndReportingByNetworkIsolationKey,EnableCrossSiteFlagNetworkIsolationKey"
      ;;
   intel)
      CHROMIUM_FLAGS+=" --use-angle=gl"
      CHROMIUM_FLAGS+=" --enable-features=VaapiVideoEncoder,VaapiVideoDecodeLinuxGL,SplitCacheByNetworkIsolationKey,SplitCodeCacheByNetworkIsolationKey,SplitHostCacheByNetworkIsolationKey,PrefetchPrivacyChanges,IsolateSandboxedIframes,StrictOriginIsolation,PartitionConnectionsByNetworkIsolationKey,PartitionHttpServerPropertiesByNetworkIsolationKey,PartitionSSLSessionsByNetworkIsolationKey,PartitionNelAndReportingByNetworkIsolationKey,EnableCrossSiteFlagNetworkIsolationKey"
      ;;
   *)
      CHROMIUM_FLAGS+=" --use-angle=gl"
      CHROMIUM_FLAGS+=" --enable-features=VaapiVideoEncoder,VaapiVideoDecodeLinuxGL,SplitCacheByNetworkIsolationKey,SplitCodeCacheByNetworkIsolationKey,SplitHostCacheByNetworkIsolationKey,PrefetchPrivacyChanges,IsolateSandboxedIframes,StrictOriginIsolation,PartitionConnectionsByNetworkIsolationKey,PartitionHttpServerPropertiesByNetworkIsolationKey,PartitionSSLSessionsByNetworkIsolationKey,PartitionNelAndReportingByNetworkIsolationKey,EnableCrossSiteFlagNetworkIsolationKey"
      ;;
esac
       

' > /usr/etc/chromium/chromium.conf



# Not temporary, keep:
echo '

CHROMIUM_FLAGS+=" --ozone-platform=wayland --no-pings --disk-cache-dir=/dev/null --disable-features=PrivacySandboxSettings4,InterestFeedV2,NTPPopularSitesBakedInContent,UsePopularSitesSuggestions,MediaDrmPreprovisioning,AutofillServerCommunication,DisableThirdPartyStoragePartitioningDeprecationTrial"

' >> /usr/etc/chromium/chromium.conf
