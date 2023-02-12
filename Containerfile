# Multi-stage build
ARG FEDORA_MAJOR_VERSION=37

## Build vanilla-first-setup
FROM ubuntu:22.04 AS build

RUN apt-get update && apt-get install -y \
    build-essential meson libadwaita-1-dev \
    gettext desktop-file-utils git

# Checkout the last tested/known working commit, in liu of an upstream release
RUN git clone https://github.com/Vanilla-OS/first-setup.git && \
    cd first-setup && git checkout bf21de5
WORKDIR first-setup
RUN meson build --prefix /usr && ninja -C build
RUN DESTDIR=/opt ninja -C build install
RUN tar cfz vanilla-first-setup.tar.gz /opt

## Build ublue-os-base
FROM quay.io/fedora-ostree-desktops/silverblue:${FEDORA_MAJOR_VERSION}
# See https://pagure.io/releng/issue/11047 for final location

## Install the VanillaOS first-setup utility
COPY --from=build /first-setup/vanilla-first-setup.tar.gz /
RUN tar xf vanilla-first-setup.tar.gz --strip-component=1 -C / && \
    chmod +x /usr/bin/vanilla-first-setup && \
    ostree container commit

COPY etc /etc

COPY ublue-firstboot /usr/bin

RUN rpm-ostree override remove firefox firefox-langpacks && \
    rpm-ostree install distrobox gnome-tweaks just && \
    sed -i 's/#AutomaticUpdatePolicy.*/AutomaticUpdatePolicy=stage/' /etc/rpm-ostreed.conf && \
    systemctl enable rpm-ostreed-automatic.timer && \
    systemctl enable flatpak-automatic.timer && \
    ostree container commit
