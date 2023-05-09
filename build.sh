#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -ouex pipefail

# Run scripts.
echo "-- Running scripts defined in recipe.yml --"
buildscripts=$(yq '.scripts[]' < /usr/etc/ublue-recipe.yml)
for script in $(echo -e "$buildscripts"); do \
    echo "Running: ${script}" && \
    /tmp/scripts/$script; \
done
echo "---"

# Remove the default firefox (from fedora) in favor of the flatpak.
rpm-ostree override remove firefox firefox-langpacks

repos=$(yq '.extrarepos[]' < /usr/etc/ublue-recipe.yml)
if [[ -n "$repos" ]]; then
    echo "-- Adding repos defined in recipe.yml --"
    for repo in $(echo -e "$repos"); do \
        wget $repo -P /etc/yum.repos.d/; \
    done
    echo "---"
fi

echo "-- Installing RPMs defined in recipe.yml --"
rpm_packages=$(yq '.rpms[]' < /usr/etc/ublue-recipe.yml)
for pkg in $(echo -e "$rpm_packages"); do \
    echo "Installing: ${pkg}" && \
    rpm-ostree install $pkg; \
done
echo "---"

# Install yafti to install flatpaks on first boot, https://github.com/ublue-os/yafti.
pip install --prefix=/usr yafti

# Add a package group for yafti using the packages defined in recipe.yml.
flatpaks=$(yq '.flatpaks[]' < /tmp/ublue-recipe.yml)
# Only try to add package groups if some flatpaks are defined in the recipe.
if [[ -n "$flatpaks" ]]; then            
    yq -i '.screens.applications.values.groups.Custom.description = "Flatpaks defined by the image maintainer"' /usr/etc/yafti.yml
    yq -i '.screens.applications.values.groups.Custom.default = true' /usr/etc/yafti.yml
    for pkg in $(echo -e "$flatpaks"); do \
        yq -i ".screens.applications.values.groups.Custom.packages += [{\"$pkg\": \"$pkg\"}]" /usr/etc/yafti.yml
    done
fi