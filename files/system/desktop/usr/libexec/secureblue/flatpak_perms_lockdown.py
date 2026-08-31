#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""Harden Flatpaks further by rejecting dangerous permissions."""

import sys
from subprocess import CalledProcessError
from typing import TYPE_CHECKING, Final

from flatpak_utils import flatpak_override

if TYPE_CHECKING:
    from files.system.usr.libexec.secureblue import utils
else:
    import utils

ask_yes_no: Final = utils.ask_yes_no


MESSAGES: dict[str, str] = {
    "warning": """\
This will configure flatpak to automatically reject most permissions
(with the exception of the Wayland socket and the Dri device).
This will also grant Flatseal access to certain permissions to make reconfiguring much easier.
NOTE: This will break just about all Flatpaks by default,
it is on you to configure them to work with this configuration.
NOTE 2: This DOES NOT enable hardened_malloc, use the harden-flatpak ujust command.
""",
    "persistent_fs_grant": """\
-- Persistent Filesystem Grant --
Note: This is to unbreak many Flatpaks by allowing the app to store persistent data in their own,
isolated home directory without accessing the user's.
Granting access to persistent home...""",
    "common_perms": """\
-- Granting Access to Common Permissions --
Note: This will grant all apps access to some permissions to ensure most apps work by default,
this also encourages the use of these permissions instead of their alternatives.
Granting access to Wayland and hardware acceleration...""",
    "dangerous_fs_perms": """\
Note: This is a VERY flawed implementation but it does cover a few blatant sandbox escape methods
(such as the .bashrc escape or mounted drive access).
It is not possible to cover all files since each file can be requested manually
and therefore must be rejected manually.""",
}

PERMISSIONS: list[tuple[str, str, list[str]]] = [
    (
        "Share",
        "unshare",
        [
            "ipc",
            "network",
        ],
    ),
    (
        "Socket",
        "nosocket",
        [
            "cups",
            "fallback-x11",
            "gpg-agent",
            "inherit-wayland-socket",
            "pcsc",
            "pulseaudio",
            "session-bus",
            "ssh-auth",
            "system-bus",
            "x11",
        ],
    ),
    (
        "Device",
        "nodevice",
        [
            "all",
            "input",
            "kvm",
            "shm",
            "usb",
        ],
    ),
    (
        "Feature",
        "disallow",
        [
            "bluetooth",
            "canbus",
            "devel",
            "multiarch",
            "per-app-dev-shm",
        ],
    ),
    (
        "Filesystem",
        "nofilesystem",
        [
            "home",
            "host",
            "host-etc",
        ],
    ),
    (
        "Dangerous Filesystem",
        "nofilesystem",
        [
            "/home",
            "/media",
            "/mnt",
            "/run",
            "/run/media",
            "/var",
            "/var/home",
            "~/.bash_profile",
            "~/.bashrc",
        ],
    ),
    (
        "Session Bus Name",
        "no-talk-name",
        [
            "ca.desrt.dconf",
            "com.canonical.AppMenu.Registrar",
            "com.canonical.Unity",
            "com.canonical.Unity.LauncherEntry",
            "com.canonical.indicator.application",
            "io.missioncenter.MissionCenter.Gatherer",
            "org.a11y.Bus",
            "org.ayatana.indicator.application",
            "org.cinnamon.ScreenSaver",
            "org.freedesktop.FileManager1",
            "org.freedesktop.Flatpak",
            "org.freedesktop.Notifications",
            "org.freedesktop.PowerManagement",
            "org.freedesktop.PowerManagement.Inhibit",
            "org.freedesktop.ScreenSaver",
            "org.freedesktop.Tracker3.Writeback",
            "org.freedesktop.impl.portal.PermissionStore",
            "org.freedesktop.secrets",
            "org.gnome.ControlCenter",
            "org.gnome.Mutter.IdleMonitor.*",
            "org.gnome.ScreenSaver",
            "org.gnome.SessionManager",
            "org.gnome.Settings",
            "org.gnome.SettingsDaemon",
            "org.gnome.SettingsDaemon.MediaKeys",
            "org.gnome.Shell.Screenshot",
            "org.gnome.Software",
            "org.gtk.vfs.*",
            "org.kde.*",
            "org.kde.JobViewServer",
            "org.kde.KGlobalSettings",
            "org.kde.StatusNotifierWatcher",
            "org.kde.kconfig.notify",
            "org.kde.kdeconnect",
            "org.kde.kded5",
            "org.kde.kded6",
            "org.kde.kiod5",
            "org.kde.kiod6",
            "org.kde.kpasswdserver",
            "org.kde.kpasswdserver6",
            "org.kde.kwalletd5",
            "org.kde.kwalletd6",
            "org.kde.kwin.Screenshot",
            "org.mate.ScreenSaver",
            "org.mpris.MediaPlayer2.haruna",
            "org.xfce.ScreenSaver",
        ],
    ),
    (
        "System Bus Name",
        "system-no-talk-name",
        [
            "org.bluez",
            "org.freedesktop.Avahi",
            "org.freedesktop.Avahi.*",
            "org.freedesktop.LogControl1",
            "org.freedesktop.NetworkManager",
            "org.freedesktop.UDisks2",
            "org.freedesktop.UPower",
            "org.freedesktop.fwupd",
            "org.freedesktop.home1",
            "org.freedesktop.hostname1",
            "org.freedesktop.import1",
            "org.freedesktop.locale1",
            "org.freedesktop.login1",
            "org.freedesktop.machine1",
            "org.freedesktop.network1",
            "org.freedesktop.oom1",
            "org.freedesktop.portable1",
            "org.freedesktop.resolve1",
            "org.freedesktop.systemd1",
            "org.freedesktop.sysupdate1",
            "org.freedesktop.timedate1",
            "org.freedesktop.timesync1",
        ],
    ),
]


def override_perms(perm_type: str, perms_list: list[str], app: str = "") -> None:
    for permission in perms_list:
        print(f"{'Granting' if app else 'Rejecting'} {permission}...")

        override_args: list[str] = [f"--{perm_type}={permission}"]
        if app:
            override_args.append(app)
        flatpak_override(*override_args)

    print()


def main() -> int:
    print(MESSAGES["warning"])
    if ask_yes_no("Would you like to proceed?"):
        try:
            for perm_name, perm_type, perms_list in PERMISSIONS:
                title: str = "Access" if "Bus" in perm_name else "Permissions"
                print(f"-- {perm_name} {title} --")

                if perm_name == "Dangerous Filesystem":
                    print(MESSAGES["dangerous_fs_perms"])

                override_perms(perm_type, perms_list)

            print(MESSAGES["persistent_fs_grant"])
            flatpak_override("--persist=.")
            print()

            print(MESSAGES["common_perms"])
            flatpak_override("--socket=wayland", "--device=dri")
            print()

            flatseal_perms: list[str] = [
                "org.freedesktop.impl.portal.PermissionStore",
                "org.gnome.Software",
            ]
            print("-- Granting Flatseal Access to Bus Names --")
            override_perms("talk-name", flatseal_perms, "com.github.tchx84.Flatseal")

            print("Done.")

        except CalledProcessError:
            print("An unexpected error occurred.")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
