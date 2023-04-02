# remove the default firefox (from fedora) in favor of the flatpak
rpm-ostree override remove firefox firefox-langpacks

echo "-- Installing RPMs defined in recipe.yml --"
rpm_packages=$(yq '.rpms[]' < /etc/ublue-recipe.yml)
for pkg in $rpm_packages; do \
    echo "Installing: ${pkg}" && \
    rpm-ostree install $pkg; \
done
echo "---"