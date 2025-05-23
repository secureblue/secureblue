#!/usr/bin/python3

"""
Flatpak permissions checks for secureblue auditing script.
"""

from typing import Final

from auditor import Status

SUCCESS: Final = Status.SUCCESS
NOTICE: Final = Status.NOTICE
WARNING: Final = Status.WARNING
FAILURE: Final = Status.FAILURE

ALIASES: Final = {
    "xdg-cache": "~/.cache",
    "xdg-config": "~/.config",
    "xdg-data": "~/.local/share",
    "xdg-desktop": "~/Desktop",
    "xdg-documents": "~/Documents",
    "xdg-downloads": "~/Downloads",
    "xdg-music": "~/Music",
    "xdg-pictures": "~/Pictures",
    "xdg-public-share": "~/Public",
    "xdg-templates": "~/Templates",
    "xdg-videos": "~/Videos",
    "home": "~",  # "~" must be the last entry in the dict
}


def parse_fs_permission(perm: str) -> tuple[str, bool, bool, bool]:
    """Parse flatpak filesystem permission string."""
    readonly = perm.endswith(":ro")
    negated = perm.startswith("!")
    if perm.endswith(":ro"):
        path = perm.removesuffix(":ro")
    elif perm.endswith(":rw"):
        path = perm.removesuffix(":rw")
    elif perm.endswith(":create"):
        path = perm.removesuffix(":create")
    else:
        path = perm
    path = path.lstrip("!").rstrip("/")
    is_alias = False
    for name, alias in ALIASES.items():
        if path.startswith(alias):
            path = path.replace(alias, name, count=1)
            is_alias = True
            break
    return path, readonly, negated, is_alias


def check_flatpak_permissions(
    name: str, perms: dict[str, list[str]], bluetooth_loaded: bool, ptrace_allowed: bool
) -> tuple[Status, list[str], list[str]]:
    """Check permissions for a single flatpak."""
    warnings = []
    recs = []
    status = SUCCESS

    if "shared" in perms:
        shared = perms["shared"]
        if "network" in shared:
            status = status.downgrade_to(NOTICE)
            warnings.append(f"{name} has network access")
            recs.append(
                f"""{name} has network access.
                        To remove it use Flatseal or run:
                        $ flatpak override -u --unshare=network {name}"""
            )
        if "ipc" in shared:
            status = status.downgrade_to(WARNING)
            warnings.append(f"{name} has inter-process communications access")
            recs.append(
                f"""{name} has inter-process communications access.
                        To remove it use Flatseal or run:
                        $ flatpak override -u --unshare=ipc {name}"""
            )

    if "sockets" in perms:
        sockets = perms["sockets"]
        if "x11" in sockets and "fallback-x11" not in sockets:
            status = status.downgrade_to(FAILURE)
            warnings.append(f"{name} has x11 access")
            recs.append(
                f"""{name} has x11 access.
                        To remove it use Flatseal or run:
                        $ flatpak override -u --nosocket=x11 {name}"""
            )
        if "pulseaudio" in sockets:
            status = status.downgrade_to(WARNING)
            warnings.append(f"{name} has access to the PulseAudio socket")
            recs.append(f"""{name} has access to the PulseAudio socket.
                        This grants access to audio and microphones.
                        To remove it use Flatseal or run:
                        $ flatpak override -u --nosocket=pulseaudio {name}""")
        if "session-bus" in sockets:
            status = status.downgrade_to(FAILURE)
            warnings.append(f"{name} has access to the D-Bus session bus")
            recs.append(
                f"""{name} has access to the D-Bus session bus.
                        To remove it use Flatseal or run:
                        $ flatpak override -u --nosocket=session-bus {name}"""
            )
        if "system-bus" in sockets:
            status = status.downgrade_to(FAILURE)
            warnings.append(f"{name} has access to the D-Bus system bus")
            recs.append(
                f"""{name} has access to the D-Bus system bus.
                        To remove it use Flatseal or run:
                        $ flatpak override -u --nosocket=system-bus {name}"""
            )

    if "devices" in perms:
        devices = perms["devices"]
        device_checks = {
            "all": {
                "status": FAILURE,
                "access": "input devices, GPUs, raw USB, and virtualization",
                "sandbox_escape": True,
                "note": f"""If GPU access is required, use device=dri instead:
                    $ flatpak override -u --device=dri {name}""",
            },
            "input": {
                "status": NOTICE,
                "access": "input devices",
                "sandbox_escape": False,
                "note": "",
            },
            "kvm": {
                "status": WARNING,
                "access": "kernel-based virtualization",
                "sandbox_escape": False,
                "note": "",
            },
            "shm": {
                "status": FAILURE,
                "access": "shared memory",
                "sandbox_escape": True,
                "note": "",
            },
            "usb": {
                "status": WARNING,
                "access": "raw USB device access",
                "sandbox_escape": True,
                "note": "",
            },
        }
        for device in devices:
            if device in device_checks:
                device_data = device_checks[device]
            else:
                continue
            status = status.downgrade_to(device_data["status"])
            warnings.append(f"{name} has device={device} permission")
            if device_data["sandbox_escape"]:
                sandbox_escape_note = "This may also be used as a sandbox escape vector."
            else:
                sandbox_escape_note = ""
            recs.append(
                f"""{name} has device={device} permission.
                        This grants access to {device_data["access"]}.
                        {sandbox_escape_note}
                        To remove it use Flatseal or run:
                        $ flatpak override -u --nodevice={device} {name}
                        {device_data["note"]}"""
            )

    ld_preloads = []
    if "LD_PRELOAD" in perms:
        for s in perms["LD_PRELOAD"]:
            if s:
                ld_preloads.append(s.rsplit("/", maxsplit=1)[-1])
    if "libhardened_malloc.so" not in ld_preloads:
        status = status.downgrade_to(WARNING)
        warnings.append(f"{name} is not requesting hardened_malloc")
        if "libhardened_malloc-light.so" in ld_preloads:
            status = status.downgrade_to(NOTICE)
            warnings.append(f"{name} is requesting hardened_malloc-light")
        elif "libhardened_malloc-pkey.so" in ld_preloads:
            status = status.downgrade_to(NOTICE)
            warnings.append(f"{name} is requesting hardened_malloc-pkey")
        recs.append(
            f"""{name} is not requesting hardened_malloc.
                    To enable it run:
                    $ ujust harden-flatpak {name}"""
        )

    if "features" in perms:
        features = perms["features"]
        if bluetooth_loaded and "bluetooth" in features:
            status = status.downgrade_to(WARNING)
            warnings.append(f"{name} has bluetooth access")
            recs.append(
                f"""{name} has bluetooth access.
                        To remove it use Flatseal or run:
                        $ flatpak override -u --disallow=bluetooth {name}"""
            )
        if ptrace_allowed and "devel" in features:
            status = status.downgrade_to(WARNING)
            warnings.append(f"{name} has ptrace access")
            recs.append(
                f"""{name} has ptrace access.
                        To remove it use Flatseal or run:
                        $ flatpak override -u --disallow=devel {name}"""
            )

    if not ("filesystems" in perms and "host-os:ro" in perms["filesystems"]):
        status = status.downgrade_to(WARNING)
        warnings.append(f"{name} is missing host-os:ro permission")
        recs.append(
            f"""{name} is missing host-os:ro permission.
                    This is required to load hardened_malloc.
                    To add it use Flatseal or run:
                    $ flatpak override -u --filesystem=host-os:ro {name}"""
        )

    arbitrary_permissions = False
    if "filesystems" in perms:
        filesystems = perms["filesystems"]
        filesystems_ro = {}
        filesystems_rw = {}
        for perm in filesystems:
            path, readonly, negated, is_alias = parse_fs_permission(perm)
            if negated:
                continue
            if readonly:
                filesystems_ro[path] = is_alias
            else:
                filesystems_rw[path] = is_alias

        dangerous_dirs: Final = {
            "host": {
                "status": FAILURE,
                "access": "all system files",
            },
            "home": {
                "status": FAILURE,
                "access": "all user files",
            },
            "xdg-config": {
                "status": FAILURE,
                "access": "other applications' configuration files",
            },
            "xdg-cache": {
                "status": FAILURE,
                "access": "other applications' cache files",
            },
            "xdg-data": {
                "status": FAILURE,
                "access": "other applications' data files",
            },
        }
        for path, dir_data in dangerous_dirs.items():
            if path in filesystems_rw:
                status = status.downgrade_to(dir_data["status"])
                is_alias = filesystems_rw[path]
                if is_alias:
                    path = path.replace(path, ALIASES[path], count=1)
                warnings.append(f"{name} has filesystem={path} permission")
                recs.append(
                    f"""{name} has filesystem={path} permission.
                        This grants access to {dir_data["access"]}.
                        To remove it use Flatseal or run:
                        $ flatpak override -u --nofilesystem={path} {name}"""
                )

        override_path = "xdg-data/flatpak/overrides"
        if override_path in filesystems_rw:
            arbitrary_permissions = True
            is_alias = filesystems_rw[override_path]
            if is_alias:
                override_path = override_path.replace("xdg-data", ALIASES["xdg-data"], count=1)
            recs.append(
                f"""{name} can modify flatpak overrides.
                    This grants the ability to acquire arbitrary permissions.
                    To remove it use Flatseal or run:
                    $ flatpak override -u --nofilesystem={override_path} {name}"""
            )

    for bus_name in ("org.freedesktop.Flatpak", "org.freedesktop.impl.portal.PermissionStore"):
        if bus_name in perms and "talk" in perms[bus_name]:
            arbitrary_permissions = True
            recs.append(
                f"""{name} can talk to {bus_name} on the session bus.
                    This grants the ability to acquire arbitrary permissions.
                    To remove it use Flatseal or run:
                    $ flatpak override -u --no-talk-name={bus_name} {name}"""
            )

    if arbitrary_permissions:
        status = status.downgrade_to(FAILURE)
        warnings.append(f"{name} can acquire arbitrary permissions")

    return status, warnings, recs
