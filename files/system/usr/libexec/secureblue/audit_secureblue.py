#!/usr/bin/python3

"""
Auditing script for secureblue. See https://secureblue.dev/ for more info.
"""

import argparse
import asyncio
import enum
import filecmp
import glob
import json
import os
import os.path
import re
import signal
import sys
import traceback

# All subprocess calls we make have trusted inputs and do not use shell=True.
import subprocess  # nosec

from collections.abc import Iterable
from typing import Final, Generator

import rpm

from auditor import AuditError, Report, Status, audit, bold, categorize, depends_on, global_audit
from audit_flatpak import check_flatpak_permissions, parse_flatpak_permissions

SUCCESS: Final = Status.SUCCESS
NOTICE: Final = Status.NOTICE
WARNING: Final = Status.WARNING
FAILURE: Final = Status.FAILURE
UNKNOWN: Final = Status.UNKNOWN


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


def is_rpm_package_installed(name: str) -> bool:
    """Checks if the given RPM package is installed."""
    ts = rpm.TransactionSet()
    matches = ts.dbMatch("name", name)
    return len(matches) > 0


class Image(enum.Enum):
    """Fedora atomic base image"""

    SILVERBLUE = enum.auto()
    KINOITE = enum.auto()
    SERICEA = enum.auto()
    COSMIC = enum.auto()
    COREOS = enum.auto()

    @classmethod
    def from_image_ref(cls, image_ref: str):
        """Convert an image reference to the corresponding Image enum instance."""
        if "silverblue" in image_ref:
            return cls.SILVERBLUE
        if "kinoite" in image_ref:
            return cls.KINOITE
        if "sericea" in image_ref:
            return cls.SERICEA
        if "cosmic" in image_ref:
            return cls.COSMIC
        if "securecore" in image_ref:
            return cls.COREOS
        return None


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
        "intel_iommu=on",
        "iommu.passthrough=0",
        "iommu.strict=1",
        "iommu=force",
        "kvm-intel.vmentry_l1d_flush=always",
        "l1d_flush=on",
        "l1tf=full,force",
        "lockdown=confidentiality",
        "loglevel=0",
        "mitigations=auto,nosmt",
        "module.sig_enforce=1",
        "page_alloc.shuffle=1",
        "pti=on",
        "random.trust_bootloader=off",
        "random.trust_cpu=off",
        "randomize_kstack_offset=on",
        "slab_nomerge",
        "spec_store_bypass_disable=on",
        "spectre_v2=on",
        "vsyscall=none",
    ]
    for karg in kargs_expected:
        status = SUCCESS if karg in kargs_current else FAILURE
        yield Report(f"Checking for {karg} karg", status)
    kargs_expected_warn = [
        "amd_iommu=force_isolation",
        "debugfs=off",
        "efi=disable_early_pci_dma",
        "gather_data_sampling=force",
        "ia32_emulation=0",
        "nosmt=force",
        "oops=panic",
    ]
    for karg in kargs_expected_warn:
        status = SUCCESS if karg in kargs_current else WARNING
        yield Report(f"Checking for {karg} karg", status)


def validate_sysctl(sysctl: str, actual: str, expected: str) -> bool:
    """Validate a sysctl value against an expected value."""
    actual = re.sub(r"\s+", " ", actual.strip())
    replace = {"disabled": "0", "enabled": "1"}.get(actual)
    if replace is not None:
        actual = replace
    if sysctl == "kernel.sysrq":
        # Both 0 and 4 are secure values for this setting. For details, see:
        # https://www.kernel.org/doc/html/latest/admin-guide/sysrq.html
        return actual in (expected, "0", "4")
    return actual == expected


@audit
def audit_sysctl():
    """Check for sysctl overrides."""
    with open("/usr/etc/sysctl.d/60-hardening.conf", "r", encoding="utf-8") as f:
        conf = f.readlines()
    sysctl_expected = {}
    for key, value in parse_config(conf):
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
            if not validate_sysctl(sysctl, actual, expected):
                status = FAILURE
                sysctl_errors.append(f"{sysctl} should be {expected}, found {actual}")
                break
    yield Report("Ensuring no sysctl overrides", status, warnings=sysctl_errors)


@audit
def audit_signed_image(state):
    """Check that the secureblue image is signed."""
    ostree_status = command_stdout("rpm-ostree", "status", "--json")
    image_ref = json.loads(ostree_status)["deployments"][0]["container-image-reference"]
    state["image"] = Image.from_image_ref(image_ref)
    if image_ref.startswith("ostree-image-signed:"):
        status = SUCCESS
        recs = None
    else:
        status = FAILURE
        recs = """The current image is not signed.
            To rebase to a signed image, download and run or re-run install_secureblue.sh
            from the secureblue GitHub repository."""
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
            rec = None
        case 0:
            status = FAILURE
            rec = f"""ptrace is allowed and {bold("unrestricted")} (ptrace_scope = 0)!
                For more info on what this means, see:
                https://www.kernel.org/doc/html/latest/admin-guide/LSM/Yama.html
                To forbid ptrace, run:
                $ ujust toggle-ptrace-scope
                To allow restricted ptrace, run the above command twice."""
        case _:
            status = WARNING
            rec = f"""ptrace is allowed, but restricted (ptrace_scope = {ptrace_scope}).
                For more info on what this means, see:
                https://www.kernel.org/doc/html/latest/admin-guide/LSM/Yama.html
                To forbid ptrace, run:
                $ ujust toggle-ptrace-scope"""
    yield Report("Ensuring ptrace is forbidden", status, recs=rec)


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
    status = SUCCESS
    warnings = []
    policy_file = "/etc/containers/policy.json"
    if not filecmp.cmp(f"/usr{policy_file}", policy_file):
        status = FAILURE
        warnings.append(f"{policy_file} has been modified")
    local_override = "~/.config/containers/policy.json"
    if os.path.isfile(os.path.expanduser(local_override)):
        status = FAILURE
        warnings.append(f"{local_override} exists")
    yield Report("Ensuring no container policy overrides", status, warnings=warnings)


@audit
def audit_unconfined_userns():
    """Ensure unconfined-domain processes cannot create user namespaces."""
    if command_stdout("ujust", "check-unconfined-userns-state") == "disabled":
        status = SUCCESS
        recs = None
    else:
        status = FAILURE
        recs = """Unconfined domain user namespace creation is permitted.
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
        recs = """Container domain user namespace creation is permitted.
                To disallow it, run:
                $ ujust toggle-container-domain-userns-creation"""
    yield Report("Ensuring container user namespace creation disallowed", status, recs=recs)


@audit
def audit_usbguard():
    """Ensure usbguard is active."""
    if command_succeeds(*"systemctl is-active --quiet usbguard".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """USBGuard is not active. To set up USBGuard, run:
            $ ujust setup-usbguard
            Caution: if you have already set up USBGuard, this will overwrite the
            existing policy."""
    yield Report("Ensuring usbguard is active", status, recs=rec)


@audit
def audit_chronyd():
    """Ensure chronyd is active."""
    if command_succeeds(*"systemctl is-active --quiet chronyd".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """chronyd is inactive.
            To start and enable it, run:
            $ systemctl enable --now chronyd"""
    yield Report("Ensuring chronyd is active", status, recs=rec)


@audit
def audit_dns():
    """Ensure system DNS resolution is active and secure."""
    rec = None
    warning = None
    if command_succeeds(*"systemctl is-active --quiet systemd-resolved".split()):
        dnssec = None
        dot = None
        conf_path = "/etc/systemd/resolved.conf.d/10-securedns.conf"
        try:
            with open(conf_path, "r", encoding="utf-8") as f:
                for key, value in parse_config(f):
                    if key == "DNSSEC":
                        dnssec = value
                    elif key == "DNSOverTLS":
                        dot = value
        except FileNotFoundError:
            status = FAILURE
        except PermissionError:
            status = UNKNOWN
            warning = f"Unable to read file {conf_path}"
        else:
            if dnssec == "true" and dot == "true":
                status = SUCCESS
            elif dot == "opportunistic":
                status = WARNING
            else:
                status = FAILURE
        if status in (WARNING, FAILURE):
            caveat = " (opportunistic DNS-over-TLS only)" if dot == "opportunistic" else ""
            rec = f"""System DNS resolution is not secure{caveat}.
                    To select a secure resolver, run:
                    $ ujust dns-selector
                    If you are using a VPN, you may want to disregard this recommendation."""
    else:
        status = FAILURE
        rec = """systemd-resolved is inactive.
                To start and enable it, run:
                $ systemctl enable --now systemd-resolved"""
    yield Report("Ensuring system DNS resolution is secure", status, warnings=warning, recs=rec)


@audit
def audit_mac_randomization():
    """Ensure MAC randomization is enabled."""
    status = FAILURE
    warning = None
    conf_path = "/etc/NetworkManager/conf.d/rand_mac.conf"
    try:
        with open(conf_path, "r", encoding="utf-8") as f:
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
    except FileNotFoundError:
        pass
    except PermissionError:
        status = UNKNOWN
        warning = f"Unable to read file {conf_path}"
    if status == FAILURE:
        rec = """MAC randomization is not enabled.
                To enable it, run:
                $ ujust toggle-mac-randomization"""
    else:
        rec = None
    yield Report("Ensuring MAC randomization is enabled", status, warnings=warning, recs=rec)


@audit
def audit_rpm_ostree_timer():
    """Ensure rpm-ostree automatic updates are enabled."""
    if command_succeeds(*"systemctl is-enabled --quiet rpm-ostreed-automatic.timer".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """rpm-ostreed-automatic.timer is disabled.
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
        rec = """podman-auto-update.timer is disabled.
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
        rec = """podman-auto-update.timer is not enabled globally.
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
        rec = """flatpak-user-update.timer is not enabled globally.
                To enable, run:
                $ systemctl enable --global flatpak-user-update.timer"""
    yield Report("Ensuring flatpak-user-update.timer is enabled globally", status, recs=rec)

    if command_succeeds(*"systemctl is-enabled --quiet flatpak-system-update.timer".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """flatpak-system-update.timer is not enabled globally.
                To enable, run:
                $ systemctl enable --now flatpak-system-update.timer"""
    yield Report("Ensuring flatpak-system-update.timer is enabled", status, recs=rec)


@audit
def audit_wheel():
    """Ensure the current user is not in the wheel group."""
    if "wheel" in command_stdout("groups").split():
        rec = f"""Current user is in the wheel group.
            To set up a separate wheel account, follow the instructions here:
            {bold("https://secureblue.dev/install#wheel")}"""
        status = FAILURE
    else:
        rec = None
        status = SUCCESS
    yield Report("Ensuring user is not a member of wheel", status, recs=rec)


@audit
@depends_on("audit_signed_image")
def audit_xwayland(state):
    """Check whether xwayland is disabled."""
    match state["image"]:
        case Image.SILVERBLUE:
            de = "GNOME"
            path = "/etc/systemd/user/org.gnome.Shell@wayland.service.d/override.conf"
        case Image.KINOITE:
            de = "KDE Plasma"
            path = "/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf"
        case Image.SERICEA:
            de = "Sway"
            path = "/etc/sway/config.d/99-noxwayland.conf"
        case _:
            return
    if os.path.isfile(path):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = f"""Xwayland is enabled for {de}. To disable, run:
            $ ujust toggle-xwayland"""
    yield Report(f"Ensuring xwayland is disabled for {de}", status, recs=rec)


@audit
@depends_on("audit_signed_image")
def audit_gnome_extensions(state):
    """Ensure GNOME user extensions are not allowed to be installed."""
    if state["image"] != Image.SILVERBLUE:
        return
    allowed = command_stdout(
        *"command -p gsettings get org.gnome.shell allow-extension-installation".split()
    )
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
        rec = """SELinux is in Permissive mode.
            To set to Enforcing mode, run:
            $ run0 setenforce 1"""
    yield Report("Ensuring SELinux is in Enforcing mode", status, recs=rec)


@audit
def audit_environment_file():
    """Ensure /etc/environment has not been modified."""
    try:
        if filecmp.cmp("/usr/etc/environment", "/etc/environment"):
            status = SUCCESS
            warning = None
        else:
            status = WARNING
            warning = "/etc/environment has been modified"
    except FileNotFoundError:
        status = WARNING
        warning = "/etc/environment has been deleted"
    except PermissionError:
        status = WARNING
        warning = "/etc/environment cannot be read"
    yield Report("Ensuring no environment file overrides", status, warnings=warning)


@audit
@depends_on("audit_signed_image")
def audit_kde_ghns(state):
    """Ensure KDE GHNS is disabled."""
    if state["image"] != Image.KINOITE:
        return
    status = FAILURE
    warning = None
    try:
        with open("/etc/xdg/kdeglobals", "r", encoding="utf-8") as f:
            for key, value in parse_config(f):
                if key == "ghns" and value == "false":
                    status = SUCCESS
                    break
    except (FileNotFoundError, PermissionError):
        status = WARNING
        warning = "/etc/xdg/kdeglobals not found or inaccessible"
    if status == FAILURE:
        rec = """KDE GHNS is enabled.
            To disable, run:
            $ ujust toggle-ghns"""
    else:
        rec = None
    yield Report("Ensuring KDE GHNS is disabled", status, warnings=warning, recs=rec)


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
    if status == SUCCESS:
        rec = None
    else:
        rec = """/etc/ld.so.preload has been modified.
            To reset it and enable hardened_malloc system-wide, run:
            $ run0 cp /usr/etc/ld.so.preload /etc/ld.so.preload"""
    yield Report(
        "Ensuring hardened_malloc is set in ld.so.preload", status, warnings=warnings, recs=rec
    )


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
            try:
                immutable = "i" in command_stdout("lsattr", "-d", path).split()[0]
            except subprocess.CalledProcessError:
                immutable = False
            if not immutable:
                unlocked_files.append(path)
    if unlocked_files:
        status = FAILURE
        rec = f"""Bash environment is not locked down.
                The following files do not appear to be immutable or do not exist:
                {"\n".join(unlocked_files)}
                To fix, run:
                $ ujust toggle-bash-environment-lockdown"""
    else:
        status = SUCCESS
        rec = None
    yield Report("Ensuring current user's bash environment is locked down", status, recs=rec)


@audit
@depends_on("audit_signed_image")
def audit_wlroot_screenshot(state):
    """Ensure wlroots screenshot support is not present."""
    if state["image"] != Image.SERICEA:
        return
    if is_rpm_package_installed("xdg-desktop-portal-wlr"):
        status = FAILURE
        rec = """wlroots screenshot support is enabled.
            To disable, run:
            $ ujust toggle-wlr-screenshot-support"""
    else:
        status = SUCCESS
        rec = None
    yield Report("Ensuring wlroots screenshot support is not present", status, recs=rec)


@audit
@categorize("flatpak")
def audit_flatpak_remotes():
    """Audit flatpak remotes."""
    if not command_succeeds(*"command -v flatpak".split()):
        return

    remotes = command_stdout(*"flatpak remotes --columns=name,url,subset".split()).split("\n")
    for remote in remotes:
        if not remote:
            continue
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


async def get_flatpak_permissions(name: str, version: str) -> str:
    """Get permissions for an installed flatpak."""
    return await async_command_stdout("flatpak", "info", "--show-permissions", name, version)


@audit
@categorize("flatpak")
@depends_on("audit_modprobe", "audit_ptrace")
async def audit_flatpak_permissions(state):
    """Audit flatpak permissions."""
    if not command_succeeds(*"command -v flatpak".split()):
        return

    flatpaks = []
    for line in command_stdout(*"flatpak list --app --columns=application,branch".split()).split(
        "\n"
    ):
        if not line:
            continue
        name, version = line.split("\t")
        flatpaks.append((name, version))
    flatpaks.sort()

    tasks = {}
    for name, version in flatpaks:
        coro = get_flatpak_permissions(name, version)
        tasks[(name, version)] = asyncio.create_task(coro, name=str((name, version)))
    # Yield flatpak permission reports in lexicographical order
    for name, version in flatpaks:
        perms_text = await tasks[(name, version)]
        perms = parse_flatpak_permissions(perms_text)
        status, warnings, recs = check_flatpak_permissions(
            name, perms, state["bluetooth_loaded"], state["ptrace_allowed"]
        )
        if version == "stable":
            report_text = f"Auditing {name}"
        else:
            report_text = f"Auditing {name} ({version})"
        yield Report(report_text, status, warnings=warnings, recs=recs)


###############################################################################
# Checks to be run go above this line.
###############################################################################


def print_err(text: str):
    """Print text to stderr in bold and red."""
    print(f"\x1b[1m\x1b[31m{text}\x1b[0m", file=sys.stderr)


def handle_sigint(_sig, _frame):
    """Gracefully handle interrupt signal."""
    print_err("\n[Audit process interrupted. Exiting.]")
    # Suppress output from exceptions in unfinished tasks
    sys.stderr = None
    sys.exit(1)


def warn_if_root():
    """If run as root, warn that this is not recommended."""
    if os.getuid() == 0:
        print_err("\n*** WARNING: Running audit script as root is not recommended. ***")
        print_err("*** Some results may be misleading or incomplete. ***\n")


def get_width() -> int:
    """Get the width in columns to be used for reports."""
    try:
        width = min(max(80, os.get_terminal_size().columns), 100)
    except OSError:
        width = 80
    return width


async def main() -> int:
    """Main entry point. Parse command-line arguments and run audit."""
    signal.signal(signal.SIGINT, handle_sigint)
    warn_if_root()
    parser = argparse.ArgumentParser()
    categories = ",".join(sorted(global_audit.categories))
    parser.add_argument("-s", "--skip", default="", help=f"skip categories ({categories})")
    parser.add_argument("-j", "--json", action="store_true", help="display output as JSON")
    args = parser.parse_args()
    skip = args.skip.split(",") if args.skip else []
    if any(cat not in global_audit.categories for cat in skip):
        print(f"Valid arguments to --skip are: {categories}", file=sys.stderr)
        sys.exit(1)
    error_occurred = False
    if args.json:
        async for report_json in global_audit.run_json(exclude=skip):
            print(report_json)
        return 0
    async for check, err in global_audit.run(exclude=skip, width=get_width()):
        print_err(f"\n*** Error in check '{check.name}' ***")
        traceback.print_exception(err)
        print_err("\n*** Continuing... ***")
        error_occurred = True
    if "flatpak" not in skip:
        print(f"Use option '{bold('--skip flatpak')}' to skip flatpak recommendations.")
    warn_if_root()
    if error_occurred:
        print_err("\n*** WARNING: Unexpected error occurred. ***")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
