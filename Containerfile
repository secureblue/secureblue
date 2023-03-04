ARG FEDORA_MAJOR_VERSION=37

FROM ghcr.io/ublue-os/silverblue-main:${FEDORA_MAJOR_VERSION}

COPY etc /etc
# COPY usr /usr

COPY ublue-firstboot /usr/bin
COPY recipe.yml /etc/ublue-recipe.yml

COPY --from=docker.io/mikefarah/yq /usr/bin/yq /usr/bin/yq

RUN rpm-ostree override remove firefox firefox-langpacks

RUN echo "-- Installing RPMs defined in recipe.yml --" && \
    rpm_packages=$(yq '.rpms[]' < /etc/ublue-recipe.yml) && \
    for pkg in $rpm_packages; do \
        echo "Installing: ${pkg}" && \
        rpm-ostree install $pkg; \
    done && \ 
    echo "---"

RUN rm -rf \
        /tmp/* \
        /var/* && \
    ostree container commit
