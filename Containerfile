ARG FEDORA_MAJOR_VERSION=38
ARG BASE_IMAGE_URL=ghcr.io/ublue-os/silverblue-main

FROM ${BASE_IMAGE_URL}:${FEDORA_MAJOR_VERSION}
ARG RECIPE

# Copy static configurations and component files.
# Warning: If you want to place anything in "/etc" of the final image, you MUST
# place them in "./usr/etc" in your repo, so that they're written to "/usr/etc"
# on the final system. That is the proper directory for "system" configuration
# templates on immutable Fedora distros, whereas the normal "/etc" is ONLY meant
# for manual overrides and editing by the machine's admin AFTER installation!
# See issue #28 (https://github.com/ublue-os/startingpoint/issues/28).
COPY usr /usr

# Copy recipe.
COPY ${RECIPE} /usr/share/ublue-os/recipe.yml

# "yq" used in build.sh and the setup-flatpaks recipe to read the recipe.yml.
# Copied from the official container image since it's not available as an RPM.
COPY --from=docker.io/mikefarah/yq /usr/bin/yq /usr/bin/yq

# Copy scripts.
RUN mkdir /tmp/scripts
COPY scripts /tmp/scripts
RUN find /tmp/scripts -type f -exec chmod +x {} \;

# Copy and run the build script.
COPY build.sh /tmp/build.sh
RUN chmod +x /tmp/build.sh && /tmp/build.sh

# Clean up and finalize container build.
RUN rm -rf \
        /tmp/* \
        /var/* && \
    ostree container commit
