#!/usr/bin/env bats

setup() {
    sudo mkdir -p /usr/share/ublue-os/just/
    sudo mkdir -p /usr/share/bluebuild/justfiles/
    sudo mkdir -p /usr/lib/ujust/


    sudo cp -fr files/system/usr/lib/ujust /usr/lib/ujust
    sudo cp -f files/system/usr/bin/ujust /usr/bin/ujust
    sudo cp -f files/system/usr/share/ublue-os/just/60-custom.just /usr/share/ublue-os/just/
    sudo cp -f files/system/usr/share/ublue-os/justfile /usr/share/ublue-os/
    sudo cp -f files/justfiles/*.just /usr/share/bluebuild/justfiles/
    for filepath in /usr/share/bluebuild/justfiles/*.just; do
        sudo sh -c "echo \"import '$filepath'\" >> /usr/share/ublue-os/just/60-custom.just"
    done
}

@test "Ensure ujust is configured correctly for tests" {
    run ujust bios
    [ "$status" -eq 0 ]
}

@test "Ensure motd toggle functions properly" {
    run ujust toggle-user-motd
    [ "$status" -eq 0 ]
    [ -f "${HOME}/.config/no-show-user-motd" ]
    run ujust toggle-user-motd
    [ "$status" -eq 0 ]
    [ ! -f "${HOME}/.config/no-show-user-motd" ]
}
