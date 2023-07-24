# This is the Containerfile for your custom image. 

# It takes in the recipe, version, and base image as arguments,
# all of which are provided by build.yml when doing builds
# in the cloud. The ARGs have default values, but changing those
# does nothing if the image is built in the cloud.

ARG FEDORA_MAJOR_VERSION=38
# Warning: changing this might not do anything for you. Read comment above.
ARG BASE_IMAGE_URL=ghcr.io/ublue-os/silverblue-main

FROM ${BASE_IMAGE_URL}:${FEDORA_MAJOR_VERSION}

# The default recipe set to the recipe's default filename
# so that `podman build` should just work for many people.
ARG RECIPE=./recipe.yml

# The default image registry to write to policy.json and cosign.yaml
ARG IMAGE_REGISTRY=ghcr.io/ublue-os

# Copy static configurations and component files.
# Warning: If you want to place anything in "/etc" of the final image, you MUST
# place them in "./usr/etc" in your repo, so that they're written to "/usr/etc"
# on the final system. That is the proper directory for "system" configuration
# templates on immutable Fedora distros, whereas the normal "/etc" is ONLY meant
# for manual overrides and editing by the machine's admin AFTER installation!
# See issue #28 (https://github.com/ublue-os/startingpoint/issues/28).
COPY usr /usr

# Copy public key
COPY cosign.pub /usr/share/ublue-os/cosign.pub

# Copy the recipe that we're building.
COPY ${RECIPE} /usr/share/ublue-os/recipe.yml

# Copy nix install script and Universal Blue wallpapers RPM from Bling image
COPY --from=ghcr.io/ublue-os/bling:latest /rpms/ublue-os-wallpapers-0.1-1.fc38.noarch.rpm /tmp/ublue-os-wallpapers-0.1-1.fc38.noarch.rpm

# Integrate bling justfiles onto image
COPY --from=ghcr.io/ublue-os/bling:latest /files/usr/share/ublue-os/just /usr/share/ublue-os/just

# Add nix installer if you want to use it
COPY --from=ghcr.io/ublue-os/bling:latest /files/usr/bin/ublue-nix* /usr/bin

# "yq" used in build.sh and the "setup-flatpaks" just-action to read recipe.yml.
# Copied from the official container image since it's not available as an RPM.
COPY --from=docker.io/mikefarah/yq /usr/bin/yq /usr/bin/yq

# Copy the build script and all custom scripts.
COPY scripts /tmp/scripts

# Run the build script, then clean up temp files and finalize container build.
RUN rpm-ostree install /tmp/ublue-os-wallpapers-0.1-1.fc38.noarch.rpm && \
        chmod +x /tmp/scripts/build.sh && \
        /tmp/scripts/build.sh && \
        rm -rf /tmp/* /var/* && \
        ostree container commit
