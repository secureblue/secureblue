ARG FEDORA_MAJOR_VERSION=37

FROM ghcr.io/ublue-os/silverblue-main:${FEDORA_MAJOR_VERSION}

COPY etc /etc
# COPY usr /usr

COPY ublue-firstboot /usr/bin
COPY recipe.yml /etc/ublue-recipe.yml

COPY --from=docker.io/mikefarah/yq /usr/bin/yq /usr/bin/yq

# copy and run the build script
COPY build.sh /tmp/build.sh
RUN chmod +x /tmp/build.sh && /tmp/build.sh

RUN rm -rf \
        /tmp/* \
        /var/* && \
    ostree container commit
