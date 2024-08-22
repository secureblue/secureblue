#!/usr/bin/env bash

# Ivo Damjanovic 2024

set -oue pipefail

# Function to display usage information
usage() {
    echo "Set Flatpak Overrides. Usage: $0 [-h] [-s] [-u] [-t] [-f] [-b]"
    echo "-s and -u set the recommended flatpak permissions"
    echo "-f and -b allow flatpak and backup tools to work"
    echo "-t allows custom themes to be used within flatpaks"
    echo "Options:"
    echo "  -h   Option H: Show usage menu"
    echo "  -s   Option S: Set System Overrides"
    echo "  -u   Option U: Set User Overrides"
    echo "  -t   Option T: Set Theme Overrides for custom theme support"
    echo "  -f   Option F: Set Flatpak tools Overrides"
    echo "  -b   Option B: Set Backup tools Overrides"
    exit 0
}

# Function for User/System Overrides
set_override() {
    local scope="$1"  # 'user' or 'system'
    local flatpak_command="flatpak override --$scope"
    
    # the base override itself, we use the same override for system and user
    # https://docs.flatpak.org/en/latest/sandbox-permissions.html
    # we disallow access to filesystem host and home, allow partly access to host read-only
    # we prefer the wayland socket and only allow x11 as fallback
    # we disallow access to IPC and Devel
    # we disallow bus socket access
    $flatpak_command \
    --nofilesystem=host --nofilesystem=home --filesystem=host-os:ro \
    --socket=wayland --socket=inherit-wayland-socket --nosocket=x11 --socket=fallback-x11 \
    --nodevice=all --device=dri --unshare=ipc --disallow=devel \
    --nosocket=system-bus --nosocket=session-bus
}

# Function for System Overrides
set_system_overrides() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "Error: Admin rights are required to set system overrides."
        exit 1
    fi
    echo "Setting system overrides..."
    set_override "system"  # Call set_override with 'system'
}

# Function for User Overrides
set_user_overrides() {
    echo "Setting user overrides..."
    set_override "user"    # Call set_override with 'user'
}

# Function for Theme Overrides
set_theme_overrides() {
    echo "Setting theme overrides..."
    # These overrides help to use a custom theme with every ui toolkit.
    # Setting the right theme, font and icons can be complex.
    # It is better to give the user a working set of options than
    # the user allowing full access to /home
    # These are not set by default and can be added by the user by the -t flag.
    flatpak override --user \
    --filesystem=xdg-data/themes:ro --filesystem=xdg-data/icons:ro \
    --filesystem=xdg-config/gtk-4.0:ro --filesystem=xdg-config/gtk-3.0:ro \
    --filesystem=xdg-config/Kvantum:ro --filesystem=xdg-config/fontconfig:ro \
    --env=XCURSOR_PATH=~/.icons
}

# Function for Flatpak tools Overrides
set_flatpak_tools_overrides() {
    # we disallow access globally but some flatpak tools need specific
    # access rights. We allow them to make it simpler for the user
    echo "Setting flatseal overrides..."
    # https://flathub.org/apps/com.github.tchx84.Flatseal
    flatpak --user override com.github.tchx84.Flatseal \
    --filesystem=/var/lib/flatpak/app:ro --filesystem=xdg-data/flatpak/app:ro \
    --filesystem=xdg-data/flatpak/overrides:create \
    --talk-name=org.gnome.Software --talk-name=org.freedesktop.impl.portal.PermissionStore
    
    echo "Setting warehouse overrides..."
    # https://flathub.org/apps/io.github.flattool.Warehouse
    flatpak --user override io.github.flattool.Warehouse \
    --filesystem=/var/lib/flatpak/app:ro --filesystem=xdg-data/flatpak/:ro \
    --filesystem=~/.var/app/ --filesystem=xdg-data/flatpak/overrides:create \
    --talk-name=org.freedesktop.Flatpak
    
    echo "Setting flatsweep overrides..."
    # https://flathub.org/apps/io.github.giantpinkrobots.flatsweep
    flatpak --user override io.github.giantpinkrobots.flatsweep \
    --filesystem=/var/lib/flatpak/app:ro --filesystem=xdg-data/flatpak/app:ro \
    --filesystem=~/.var/app/:rw
    
    echo "Setting jdflatpaksnapshot overrides..."
    # https://flathub.org/apps/page.codeberg.JakobDev.jdFlatpakSnapshot
    flatpak --user override page.codeberg.JakobDev.jdFlatpakSnapshot \
    --filesystem=/var/lib/flatpak/app:ro --filesystem=xdg-data/flatpak/:ro \
    --filesystem=~/.var/app/:rw --talk-name=org.freedesktop.Flatpak
}

# Function for backup tools Overrides
set_backup_tools_overrides() {
    # we disallow access globally but some backup tools need specific
    # access rights. We allow them to make it simpler for the user
    # Backups are important
    echo "Setting saveDesktop overrides..."
    # https://flathub.org/apps/io.github.vikdevelop.SaveDesktop
    flatpak --user override io.github.vikdevelop.SaveDesktop \
    # load Desktop environment config files
    --filesystem=~/.config \
    --filesystem=~/.local/share \
    # to be able to select destination for saving configuration in also these directories
    --filesystem=xdg-download \
    --filesystem=xdg-documents \
    --filesystem=xdg-desktop \
    # save all themes installed in home folder
    --filesystem=~/.themes:create \
    --filesystem=~/.icons:create \
    # save cinnamon config in home directory
    --filesystem=~/.cinnamon:create \
    --filesystem=~/.xfce4:create \
    --filesystem=~/.fonts:create \
    # save a list of installed flatpak apps
    --filesystem=/var/lib/flatpak:ro \
    --filesystem=~/.local/share/flatpak/app:ro \
    # save user data of installed flatpak apps
    --filesystem=~/.var/app:ro \
    # ensuring to FileChooserNative will work correctly
    --talk-name=org.freedesktop.FileManager1 \
    --env=DCONF_USER_CONFIG_DIR=.config/dconf \
    --filesystem=xdg-run/dconf \
    --talk-name=ca.desrt.dconf
    
    echo "Setting PikaBackup overrides..."
    # https://flathub.org/apps/org.gnome.World.PikaBackup
    flatpak --user override org.gnome.World.PikaBackup \
    # Read files for to backup
    # Host has to be writable because configs become unwriteable otherwise
    --filesystem=host \
    --filesystem=home \
    --filesystem=/var:ro \
    # flatpak puts a tmpfs here to hide other apps
    # it contains configs of all flatpak apps
    --filesystem=~/.var/app \
    # flatpak puts a tmpfs here to hide all apps
    # it contains the apps and overrides for app priviledges
    --filesystem=xdg-data/flatpak:ro \
    # SSH backups etc.
    --share=network \
    # SSH-keys etc
    --socket=ssh-auth \
    # GVfs (gio::Device etc)
    --talk-name=org.gtk.vfs.* \
    --filesystem=xdg-run/gvfs \
    --filesystem=xdg-run/gvfsd \
    # UPower (OnBattery)
    --system-talk-name=org.freedesktop.UPower \
    # fusermount for mounting repositories
    --device=all \
    --talk-name=org.freedesktop.Flatpak.* \
    # Location into which to mount repositories
    --filesystem=xdg-run/pika-backup:create \
    # Show GNOME shell dialogs for unmount operations instead of very old GTK internal ones
    --talk-name=org.gtk.MountOperationHandler
    
    echo "Setting Deja Dup overrides..."
    # https://flathub.org/apps/org.gnome.DejaDup
    flatpak --user override org.gnome.DejaDup \
    # Filesystem access
    --filesystem=host \
    --filesystem=home \
    # flatpak hides these even with 'host' above
    --filesystem=~/.var/app/ \
    # GVfs
    --filesystem=xdg-run/gvfs \
    --filesystem=xdg-run/gvfsd \
    --talk-name=org.gtk.MountOperationHandler \
    --talk-name=org.gtk.vfs.* \
    # Network access
    --share=network \
    --socket=ssh-auth
    
    echo "Setting syncbackup overrides..."
    # https://flathub.org/apps/com.darhon.syncbackup
    flatpak --user override com.darhon.syncbackup \
    --share=network \
    --filesystem=host \
    --filesystem=home
    
    echo "Setting celeste overrides..."
    # https://flathub.org/apps/com.hunterwittenborn.Celeste
    flatpak --user override com.hunterwittenborn.Celeste \
    --share=network \
    --filesystem=host \
    --filesystem=home \
    # DBus sockets we need for tray access.
    --talk-name=org.kde.StatusNotifierWatcher \
    --talk-name=com.canonical.AppMenu.Registrar \
    --talk-name=com.canonical.indicator.application \
    --talk-name=com.canonical.Unity.LauncherEntry \
    --own-name=org.kde.*
    
    echo "Setting vorta overrides..."
    # https://flathub.org/apps/com.borgbase.Vorta
    flatpak --user override com.borgbase.Vorta \
    --share=network \
    --filesystem=host \
    --filesystem=home \
    --filesystem=~/.var/app/ \
    --talk-name=org.freedesktop.DBus.* \
    --talk-name=org.freedesktop.Flatpak.* \
    --talk-name=org.freedesktop.secrets \
    --talk-name=org.kde.kwalletd5 \
    --talk-name=org.kde.StatusNotifierWatcher \
    --system-talk-name=org.freedesktop.login1 \
    --system-talk-name=org.freedesktop.NetworkManager \
    --socket=ssh-auth \
    --talk-name=org.freedesktop.Notifications
}

# Check if no flags were provided
# We use this to set the default overrides at build time for
# system and user but not the other options.
if [ $# -eq 0 ]; then
    echo "No options provided. Running system and user overrides."
    if [ "$(id -u)" -eq 0 ]; then
        echo "Info: Admin rights available."
        set_system_overrides
    fi
    set_user_overrides
    exit 0
fi

# Process command-line options
while getopts ":hsutfb" opt; do
    case ${opt} in
        h ) 
            usage
            ;;
        s ) 
            set_system_overrides
            ;;
        u ) 
            set_user_overrides
            ;;
        t ) 
            set_theme_overrides
            ;;
        f ) 
            set_flatpak_tools_overrides
            ;;
        b ) 
            set_backup_tools_overrides
            ;;
        \? ) 
            echo "Invalid option: -$OPTARG" 1>&2
            usage
            ;;
    esac
done

# Shift processed options away
shift $((OPTIND -1))

echo "Override processes completed."