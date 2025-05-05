#!/usr/bin/env python3

"""
Auditing script for secureblue. See https://secureblue.dev/ for more info.
"""

import argparse
import asyncio
import filecmp
import glob
import os.path
import re
import signal
import sys

# All subprocess calls we make have trusted inputs and do not use shell=True.
import subprocess  # nosec

from collections.abc import Iterable
from typing import Final, Generator

from auditor import AuditError, Report, Status, audit, bold, categorize, depends_on, global_audit

SUCCESS: Final = Status.SUCCESS
WARNING: Final = Status.WARNING
FAILURE: Final = Status.FAILURE


def command_stdout(*args: str, check: bool = True) -> str:
    """Run a command in the shell and return the contents of stdout."""
    # We only call this with trusted inputs and do not set shell=True.
    return subprocess.run(args, capture_output=True, check=check, text=True).stdout.strip()  # nosec


class AsyncProcessError(AuditError):
    """An asynchronous subprocess command returned a nonzero exit code."""


async def async_command_stdout(cmd: str, *args: str, check: bool = True) -> str:
    """Asynchronously run a command in the shell and return the contents of stdout."""
    sub = await asyncio.create_subprocess_exec(
        cmd, *args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    await sub.wait()
    if check and sub.returncode != 0:
        err = f"async command `{cmd} {' '.join(args)}` returned nonzero exit code {sub.returncode}"
        raise AsyncProcessError(err)
    if sub.stdout is None:
        err = f"Failed to get stdout for async command `{cmd} {' '.join(args)}`"
        raise AsyncProcessError(err)
    output = await sub.stdout.read()
    return output.decode("utf-8", errors="replace").strip()


def command_succeeds(*args: str) -> bool:
    """Run a command in the shell and return the contents of stdout."""
    # We only call this with trusted inputs and do not set shell=True.
    return subprocess.run(args, capture_output=True, check=False).returncode == 0  # nosec


def parse_config(
    stream: Iterable[str], *, sep: str = "=", comment: str = "#"
) -> Generator[tuple[str, str | None]]:
    """
    Parse a text stream as a simple configuration file, yielding a sequence of keys and values
    separated by the given separator ("=" by default).
    """
    for line in stream:
        line = line.strip()
        if not line or line.startswith(comment):
            continue
        split = line.split(sep, maxsplit=1)
        key = split[0].strip()
        if len(split) == 2:
            value = split[1].strip()
        else:
            value = None
        yield key, value


###############################################################################
# Checks to be run go below this line.
###############################################################################


@audit
@categorize("kargs")
def audit_kargs():
    """Check for hardened kernel arguments."""
    kargs_current = command_stdout("rpm-ostree", "kargs").split()
    kargs_expected = [
        "init_on_alloc=1",
        "init_on_free=1",
        "slab_nomerge",
        "page_alloc.shuffle=1",
        "randomize_kstack_offset=on",
        "vsyscall=none",
        "lockdown=confidentiality",
        "random.trust_cpu=off",
        "random.trust_bootloader=off",
        "iommu=force",
        "intel_iommu=on",
        "amd_iommu=force_isolation",
        "iommu.passthrough=0",
        "iommu.strict=1",
        "pti=on",
        "module.sig_enforce=1",
        "mitigations=auto,nosmt",
        "spectre_v2=on",
        "spec_store_bypass_disable=on",
        "l1d_flush=on",
        "gather_data_sampling=force",
        "efi=disable_early_pci_dma",
        "debugfs=off",
        "ia32_emulation=0",
        "l1tf=full,force",
        "kvm-intel.vmentry_l1d_flush=always",
    ]
    for karg in kargs_expected:
        status = SUCCESS if karg in kargs_current else FAILURE
        yield Report(f"Checking for {karg} karg", status)


def validate_sysctl(actual: str, expected: str) -> bool:
    """Validate a sysctl value against an expected value."""
    actual = re.sub(r"\s+", " ", actual.strip())
    return actual in (expected, "disabled")


@audit
def audit_sysctl():
    """Check for sysctl overrides."""
    with open("/usr/etc/sysctl.d/60-hardening.conf", "r", encoding="utf-8") as f:
        conf = f.readlines()
    sysctl_expected = {}
    for key, value in parse_config(conf):
        if value is None:
            raise ValueError(f"Failed to parse sysctl value for {key}")
        sysctl_expected[key] = value
    status = SUCCESS
    sysctl_errors = []
    with open("/etc/sysctl.d/60-hardening.conf", "r", encoding="utf-8") as f:
        etc_conf = f.readlines()
    if conf != etc_conf:
        status = WARNING
        sysctl_errors.append("/etc/sysctl.d/60-hardening.conf has been modified")
    for sysctl, expected in sysctl_expected.items():
        sysctl_path = f"/proc/sys/{sysctl.replace('.', '/')}"
        for path in glob.iglob(sysctl_path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    actual = f.read().strip()
            except PermissionError:
                continue
            if not validate_sysctl(actual, expected):
                status = FAILURE
                sysctl_errors.append(f"{sysctl} should be {expected}, found {actual}")
                break
    yield Report("Ensuring no sysctl overrides", status, warnings=sysctl_errors)


@audit
def audit_signed_image():
    """Check that the secureblue image is signed."""
    ostree_status = command_stdout("rpm-ostree", "status")
    if "● ostree-image-signed" in ostree_status:
        status = SUCCESS
        recs = None
    else:
        status = FAILURE
        recs = """The current image is not signed.
            To rebase to a signed image download and run or re-run install_secureblue.sh
            from the secureblue github."""
    yield Report("Ensuring a signed image is in use", status, recs=recs)


@audit
def audit_modprobe(state):
    """Check that the kernel module blacklist has not been overridden."""
    with open("/usr/etc/modprobe.d/blacklist.conf", "r", encoding="utf-8") as f:
        conf = f.readlines()
    blacklisted_modules = []
    for line in conf:
        words = line.strip().split()
        if words and words[0] in ["blacklist", "install"]:
            blacklisted_modules.append(words[1])
    unwanted_modules = []
    with open("/proc/modules", "r", encoding="utf-8") as f:
        for line in f:
            mod = line.split()[0]
            if mod in blacklisted_modules:
                unwanted_modules.append(mod)
    unwanted_modules.sort()
    status = SUCCESS
    warnings = []
    with open("/etc/modprobe.d/blacklist.conf", "r", encoding="utf-8") as f:
        if f.readlines() != conf:
            status = WARNING
            warnings.append("/etc/modprobe.d/blacklist.conf has been modified")
    for mod in unwanted_modules:
        status = FAILURE
        warnings.append(f"{mod} is in blacklist.conf but it is loaded")
    state["bluetooth_loaded"] = "bluetooth" in unwanted_modules
    yield Report("Ensuring no modprobe overrides", status, warnings=warnings)


@audit
def audit_ptrace(state):
    """Ensure the ptrace syscall is forbidden."""
    with open("/proc/sys/kernel/yama/ptrace_scope", "r", encoding="utf-8") as f:
        ptrace_scope = int(f.read())
    state["ptrace_allowed"] = ptrace_scope < 3
    match ptrace_scope:
        case 3:
            status = SUCCESS
        case 0:
            status = FAILURE
        case _:
            status = WARNING
    yield Report("Ensuring ptrace is forbidden", status)


@audit
def audit_authselect():
    """Ensure no authselect overrides have been made."""
    cmp = filecmp.dircmp("/usr/etc/authselect", "/etc/authselect", shallow=False, ignore=[])
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        status = FAILURE
    else:
        status = SUCCESS
    yield Report("Ensuring no authselect overrides", status)


@audit
def audit_container_policy():
    """Ensure container policy has not been modified."""
    unmodified = filecmp.cmp("/usr/etc/containers/policy.json", "/etc/containers/policy.json")
    local_override = os.path.isfile(os.path.expanduser("~/.config/containers/policy.json"))
    if unmodified and not local_override:
        status = SUCCESS
    else:
        status = FAILURE
    yield Report("Ensuring no container policy overrides", status)


@audit
def audit_unconfined_userns():
    """Ensure unconfined-domain processes cannot create user namespaces."""
    if command_stdout("ujust", "check-unconfined-userns-state") == "disabled":
        status = SUCCESS
        recs = None
    else:
        status = FAILURE
        recs = """Unconfined domain user namespace creation is permitted
                To disallow it, run:
                $ ujust toggle-unconfined-domain-userns-creation"""
    yield Report("Ensuring unconfined user namespace creation disallowed", status, recs=recs)


@audit
def audit_container_userns():
    """Ensure container-domain processes cannot create user namespaces."""
    if command_stdout("ujust", "check-container-userns-state") == "disabled":
        status = SUCCESS
        recs = []
    else:
        status = WARNING
        recs = """Container domain user namespace creation is permitted
                To disallow it, run:
                $ ujust toggle-container-domain-userns-creation"""
    yield Report("Ensuring container user namespace creation disallowed", status, recs=recs)


@audit
def audit_usbguard():
    """Ensure usbguard is active."""
    if command_succeeds(*"systemctl is-active --quiet usbguard".split()):
        status = SUCCESS
    else:
        status = FAILURE
    yield Report("Ensuring usbguard is active", status)


@audit
def audit_chronyd():
    """Ensure chronyd is active."""
    if command_succeeds(*"systemctl is-active --quiet chronyd".split()):
        status = SUCCESS
    else:
        status = FAILURE
    yield Report("Ensuring chronyd is active", status)


@audit
def audit_dns():
    """Ensure system DNS resolution is active and secure."""
    rec = None
    if command_succeeds(*"systemctl is-active --quiet systemd-resolved".split()):
        dnssec = False
        dot = False
        try:
            with open("/etc/systemd/resolved.conf.d/10-securedns.conf", "r", encoding="utf-8") as f:
                for key, value in parse_config(f):
                    if key == "DNSSEC" and value == "true":
                        dnssec = True
                    if key == "DNSOverTLS" and value == "true":
                        dot = True
                    if dnssec and dot:
                        break
        except (FileNotFoundError, PermissionError):
            pass
        if dnssec and dot:
            status = SUCCESS
        else:
            status = FAILURE
            rec = """System DNS resolution is not secure
                    To select a secure resolver, run:
                    $ ujust dns-selector"""
    else:
        status = FAILURE
        rec = """systemd-resolved is inactive
                To start and enable it, run:
                $ systemctl enable --now systemd-resolved"""
    yield Report("Ensuring system DNS resolution is secure", status, recs=rec)


@audit
def audit_mac_randomization():
    """Ensure MAC randomization is enabled."""
    status = FAILURE
    try:
        with open("/etc/NetworkManager/conf.d/rand_mac.conf", "r", encoding="utf-8") as f:
            ethernet = False
            wifi = False
            for key, value in parse_config(f):
                if key == "ethernet.cloned-mac-address" and value in ["random", "stable"]:
                    ethernet = True
                if key == "wifi.cloned-mac-address" and value in ["random", "stable"]:
                    wifi = True
                if ethernet and wifi:
                    status = SUCCESS
                    break
    except (FileNotFoundError, PermissionError):
        pass
    if status == FAILURE:
        rec = """MAC randomization is not enabled
                To enable it, run:
                $ ujust toggle-mac-randomization"""
    else:
        rec = None
    yield Report("Ensuring MAC randomization is enabled", status, recs=rec)


@audit
def audit_rpm_ostree_timer():
    """Ensure rpm-ostree automatic updates are enabled."""
    if command_succeeds(*"systemctl is-enabled --quiet rpm-ostreed-automatic.timer".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """rpm-ostreed-automatic.timer is disabled
                To enable, run:
                $ systemctl enable --now rpm-ostreed-automatic.timer"""
    yield Report("Ensuring rpm-ostreed-automatic.timer is enabled", status, recs=rec)


@audit
def audit_podman_auto_update():
    """Ensure podman automatic updates are enabled."""
    if command_succeeds(*"systemctl is-enabled --quiet podman-auto-update.timer".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """podman-auto-update.timer is disabled
                To enable, run:
                $ systemctl enable --now podman-auto-update.timer"""
    yield Report("Ensuring podman-auto-update.timer is enabled", status, recs=rec)


@audit
def audit_podman_global_auto_update():
    """Ensure podman automatic updates are enabled globally."""
    if command_succeeds(*"systemctl --global is-enabled --quiet podman-auto-update.timer".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """podman-auto-update.timer is not enabled globally
                To enable, run:
                $ systemctl enable --global podman-auto-update.timer"""
    yield Report("Ensuring podman-auto-update.timer is enabled globally", status, recs=rec)


@audit
def audit_flatpak_auto_update():
    """Ensure flatpak automatic updates are enabled."""
    if not command_succeeds(*"command -v flatpak".split()):
        return
    if command_succeeds(*"systemctl --global is-enabled --quiet flatpak-user-update.timer".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """flatpak-user-update.timer is not enabled globally
                To enable, run:
                $ systemctl enable --global flatpak-user-update.timer"""
    yield Report("Ensuring flatpak-user-update.timer is enabled globally", status, recs=rec)

    if command_succeeds(*"systemctl is-enabled --quiet flatpak-system-update.timer".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """flatpak-system-update.timer is not enabled globally
                To enable, run:
                $ systemctl enable --now flatpak-system-update.timer"""
    yield Report("Ensuring flatpak-system-update.timer is enabled", status, recs=rec)


@audit
def audit_wheel():
    """Ensure the current user is not in the wheel group."""
    if "wheel" in command_stdout("groups").split():
        status = FAILURE
    else:
        status = SUCCESS
    yield Report("Ensuring user is not a member of wheel", status)


@audit
def audit_xwayland():
    """Check whether xwayland is disabled."""
    paths = {
        "GNOME": "/etc/systemd/user/org.gnome.Shell@wayland.service.d/override.conf",
        "KDE Plasma": "/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf",
        "Sway": "/etc/sway/config.d/99-noxwayland.conf",
    }
    for de, path in paths.items():
        if os.path.isfile(path):
            status = SUCCESS
            rec = None
        else:
            status = FAILURE
            rec = f"""Xwayland is enabled for {de}. To disable, run:
                $ ujust toggle-xwayland"""
        yield Report(f"Ensuring xwayland is disabled for {de}", status, recs=rec)


@audit
def audit_gnome_extensions():
    """Ensure GNOME user extensions are not allowed to be installed."""
    if not command_succeeds(*"command -v gnome-shell".split()):
        return
    allowed = command_stdout(*"gsettings get org.gnome.shell allow-extension-installation".split())
    if allowed == "false":
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """GNOME user extensions are enabled. To disable, run:
            $ ujust toggle-gnome-extensions"""
    yield Report("Ensuring GNOME user extensions are disabled", status, recs=rec)


@audit
def audit_selinux():
    """Ensure SELinux is in enforcing mode."""
    if command_stdout("getenforce") == "Enforcing":
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """SELinux is in Permissive mode
            To set to Enforcing mode, run:
            $ run0 setenforce 1"""
    yield Report("Ensuring SELinux is in Enforcing mode", status, recs=rec)


@audit
def audit_environment_file():
    """Ensure /etc/environment has not been modified."""
    if filecmp.cmp("/usr/etc/environment", "/etc/environment"):
        status = SUCCESS
    else:
        status = WARNING
    yield Report("Ensuring no environment file overrides", status)


@audit
def audit_kde_ghns():
    """Ensure KDE GHNS is disabled."""
    try:
        with open("/etc/xdg/kdeglobals", "r", encoding="utf-8") as f:
            status = FAILURE
            rec = None
            for key, value in parse_config(f):
                if key == "ghns" and value == "false":
                    status = SUCCESS
                    rec = """KDE GHNS is enabled
                        To disable, run:
                        $ ujust toggle-ghns"""
                    break
    except FileNotFoundError:
        return
    yield Report("Ensuring KDE GHNS is disabled", status, recs=rec)


@audit
def audit_hardened_malloc():
    """Ensure hardened_malloc is set to be preloaded in place of the default system malloc."""
    warnings = []
    try:
        with open("/etc/ld.so.preload", "r", encoding="utf-8") as f:
            preloaded = f.read().split()
    except FileNotFoundError:
        status = FAILURE
        warnings.append("ld.so.preload not found")
    except PermissionError:
        status = FAILURE
        warnings.append("Permission denied to read ld.so.preload")
    else:
        if preloaded == ["libhardened_malloc.so"]:
            status = SUCCESS
        elif "libhardened_malloc.so" in preloaded:
            status = WARNING
            warnings.append("hardened_malloc set, but ld.so.preload has been modified")
        elif "libhardened_malloc-light.so" in preloaded:
            status = WARNING
            warnings.append("'light' variant of hardened_malloc set")
        elif "libhardened_malloc-pkey.so" in preloaded:
            status = WARNING
            warnings.append("'pkey' variant of hardened_malloc set")
        else:
            status = FAILURE
            warnings.append("hardened_malloc not set")
    yield Report("Ensuring hardened_malloc is set in ld.so.preload", status, warnings=warnings)


@audit
def audit_secureboot():
    """Ensure secureboot is enabled."""
    if command_stdout("mokutil", "--sb-state", check=False) == "SecureBoot enabled":
        status = SUCCESS
    else:
        status = FAILURE
    yield Report("Ensuring secure boot is enabled", status)


@audit
def audit_bash_env_lockdown():
    """Ensure the current user's bash environment is locked down."""
    bash_env_paths = map(
        os.path.expanduser,
        [
            "~/.bashrc",
            "~/.bash_profile",
            "~/.config/bash_completion",
            "~/.profile",
            "~/.bash_logout",
            "~/.bash_login",
            "~/.bashrc.d/",
            "~/.config/environment.d/",
        ],
    )
    unlocked_files = []
    for path in bash_env_paths:
        if not os.path.exists(path):
            unlocked_files.append(path)
        elif not os.path.isfile(path) and not os.path.isdir(path):
            unlocked_files.append(path)
        else:
            if path[-1] == "/":
                cmd = ["lsattr", "-d", path]
            else:
                cmd = ["lsattr", path]
            try:
                immutable = "i" in command_stdout(*cmd).split()[0]
            except subprocess.CalledProcessError:
                immutable = False
            if not immutable:
                unlocked_files.append(path)
    if unlocked_files:
        status = FAILURE
        rec = f"""Bash environment is not locked down
                The following files do not appear to be immutable or do not exist:
                {"\n".join(unlocked_files)}
                To fix, run:
                $ ujust toggle-bash-environment-lockdown"""
    else:
        status = SUCCESS
        rec = None
    yield Report("Ensuring current user's bash environment is locked down", status, recs=rec)


@audit
@categorize("flatpak")
def audit_flatpak_remotes():
    """Audit flatpak remotes."""
    if not command_succeeds(*"command -v flatpak".split()):
        return

    remotes = command_stdout(*"flatpak remotes --columns=name,url,subset".split()).split("\n")
    for remote in remotes:
        name, url, subset = remote.split("\t")
        warnings = []
        if url not in [
            "https://dl.flathub.org/repo/",
            "https://dl.flathub.org/beta-repo/",
        ]:
            status = FAILURE
            warnings.append(f"{name} is configured with an unknown url")
        elif subset != "verified":
            status = FAILURE
            warnings.append(f"{name} is not a verified repo")
        else:
            status = SUCCESS
        yield Report(f"Auditing flatpak remote {name}", status, warnings=warnings)


async def check_flatpak_permissions(name, version, state):
    """Check permissions for a single flatpak."""
    warnings = []
    recs = []
    status = SUCCESS
    perms_text = await async_command_stdout("flatpak", "info", "--show-permissions", name, version)
    perms = {}
    for line in perms_text.split("\n"):
        if not line or line[0] in "[]#":
            continue
        key, value_str = line.split("=", maxsplit=1)
        vals = [val for val in value_str.split(";") if val]
        perms[key] = vals

    if "shared" in perms:
        shared = perms["shared"]
        if "network" in shared:
            if status != FAILURE:
                status = WARNING
            warnings.append(f"{name} has network access")
            recs.append(
                f"""{name} has network access
                        To remove it use Flatseal or run:
                        $ flatpak override -u --unshare=network {name}"""
            )
        if "ipc" in shared:
            status = FAILURE
            warnings.append(f"{name} has inter-process communications access")
            recs.append(
                f"""{name} has inter-process communications access
                        To remove it use Flatseal or run:
                        $ flatpak override -u --unshare=ipc {name}"""
            )

    if "sockets" in perms:
        sockets = perms["sockets"]
        if "x11" in sockets and "fallback-x11" not in sockets:
            status = FAILURE
            warnings.append(f"{name} has x11 access")
            recs.append(
                f"""{name} has x11 access
                        To remove it use Flatseal or run:
                        $ flatpak override -u --nosocket=x11 {name}"""
            )
        if "session-bus" in sockets:
            if status != FAILURE:
                status = WARNING
            warnings.append(f"{name} has access to the D-Bus session bus")
            recs.append(
                f"""{name} has access to the D-Bus session bus
                        To remove it use Flatseal or run:
                        $ flatpak override -u --nosocket=session-bus {name}"""
            )
        if "system-bus" in sockets:
            if status != FAILURE:
                status = WARNING
            warnings.append(f"{name} has access to the D-Bus system bus")
            recs.append(
                f"""{name} has access to the D-Bus system bus
                        To remove it use Flatseal or run:
                        $ flatpak override -u --nosocket=system-bus {name}"""
            )

    ld_preloads = []
    if "LD_PRELOAD" in perms:
        for s in perms["LD_PRELOAD"]:
            if s:
                ld_preloads.append(s.rsplit("/", maxsplit=1)[-1])
    if "libhardened_malloc.so" not in ld_preloads:
        status = FAILURE
        warnings.append(f"{name} is not requesting hardened_malloc")
        if "libhardened_malloc-light.so" in ld_preloads:
            status = WARNING
            warnings.append(f"{name} is requesting hardened_malloc-light")
        elif "libhardened_malloc-pkey.so" in ld_preloads:
            status = WARNING
            warnings.append(f"{name} is requesting hardened_malloc-pkey")
        recs.append(
            f"""{name} is not requesting hardened_malloc
                    To enable it run:
                    $ ujust harden-flatpak {name}"""
        )

    if not ("filesystems" in perms and "host-os:ro" in perms["filesystems"]):
        status = FAILURE
        warnings.append(f"{name} is missing host-os:ro permission")
        recs.append(
            f"""{name} is missing host-os:ro permission
                    This is required to load hardened_malloc.
                    To add it use Flatseal or run:
                    $ flatpak override -u --filesystem=host-os:ro {name}"""
        )

    if "features" in perms:
        features = perms["features"]
        if state["bluetooth_loaded"] and "bluetooth" in features:
            status = FAILURE
            warnings.append(f"{name} has bluetooth access")
            recs.append(
                f"""{name} has bluetooth access
                        To remove it use Flatseal or run:
                        $ flatpak override -u --disallow=bluetooth {name}"""
            )
        if state["ptrace_allowed"] and "devel" in features:
            status = FAILURE
            warnings.append(f"{name} has ptrace access")
            recs.append(
                f"""{name} has ptrace access
                        To remove it use Flatseal or run:
                        $ flatpak override -u --disallow=devel {name}"""
            )

    if "devices" in perms and "all" in perms["devices"]:
        if status != FAILURE:
            status = WARNING
        warnings.append(f"""{name} has device=all permission""")
        recs.append(
            f"""{name} has device=all permission
                    This grants access to input devices, GPUs, raw USB, and virtualization
                    This may also be used as a sandbox escape vector
                    To remove it use Flatseal or run:
                    $ flatpak override -u --nodevice=all {name}
                    If GPU access is required, use device=dri instead:
                    $ flatpak override -u --device=dri {name}"""
        )

    return status, warnings, recs


@audit
@categorize("flatpak")
@depends_on("audit_modprobe", "audit_ptrace")
async def audit_flatpak_permissions(state):
    """Audit flatpak permissions."""
    if not command_succeeds(*"command -v flatpak".split()):
        return

    flatpaks = []
    for line in command_stdout(*"flatpak list --columns=application,branch".split()).split("\n"):
        name, version = line.split("\t")
        flatpaks.append((name, version))
    flatpaks.sort()

    tasks = {}
    for name, version in flatpaks:
        coro = check_flatpak_permissions(name, version, state)
        tasks[(name, version)] = asyncio.create_task(coro, name=str((name, version)))
    # Yield flatpak permission reports in lexicographical order
    for name, version in flatpaks:
        status, warnings, recs = await tasks[(name, version)]
        yield Report(f"Auditing {name} ({version})", status, warnings=warnings, recs=recs)


###############################################################################
# Checks to be run go above this line.
###############################################################################


def handle_sigint(_sig, _frame):
    """Gracefully handle interrupt signal."""
    print(bold("\n[Audit process interrupted. Exiting.]"), file=sys.stderr)
    # Suppress output from exceptions in unfinished tasks
    sys.stderr = None
    sys.exit(1)


async def main():
    """Main entry point. Parse command-line arguments and run audit."""
    signal.signal(signal.SIGINT, handle_sigint)
    parser = argparse.ArgumentParser()
    categories = ",".join(sorted(global_audit.categories))
    parser.add_argument("-s", "--skip", default="", help=f"skip categories ({categories})")
    args = parser.parse_args()
    skip = args.skip.split(",") if args.skip else []
    if any(cat not in global_audit.categories for cat in skip):
        print(f"Valid arguments to --skip are: {categories}", file=sys.stderr)
        sys.exit(1)
    await global_audit.run(exclude=skip)
    if "flatpak" not in skip:
        print(f"Use option '{bold('--skip flatpak')}' to skip flatpak recommendations.")


if __name__ == "__main__":
    asyncio.run(main())
