#!/usr/bin/python3

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Auditing script for secureblue. See https://secureblue.dev/ for more info.
"""

import argparse
import asyncio
import filecmp
import glob
import json
import os
import os.path
import signal
import stat

# All subprocess calls we make have trusted inputs and do not use shell=True.
import subprocess  # nosec
import sys
import traceback
from typing import Final

from audit_flatpak import check_flatpak_permissions, parse_flatpak_permissions
from auditor import Report, Status, audit, bold, categorize, depends_on, global_audit
from utils import (
    Image,
    command_stdout,
    command_succeeds,
    get_flatpak_permissions,
    get_legend,
    get_width,
    parse_config,
    print_err,
    validate_sysctl,
    warn_if_root,
)

PASS: Final = Status.PASS
INFO: Final = Status.INFO
WARN: Final = Status.WARN
FAIL: Final = Status.FAIL
UNKNOWN: Final = Status.UNKNOWN


@audit
def audit_kargs():
    """Check for hardened kernel arguments."""
    status = PASS
    warnings = []
    rec = None

    kargs_current = frozenset(command_stdout("rpm-ostree", "kargs").split())
    kargs_expected = (
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
        "rd.emergency=halt",
        "rd.shell=0",
        "slab_nomerge",
        "spec_store_bypass_disable=on",
        "spectre_v2=on",
        "vsyscall=none",
    )
    for karg in kargs_expected:
        if karg not in kargs_current:
            status = status.downgrade_to(FAIL)
            warnings.append(f"Missing kernel argument: {karg}")

    karg_32bit = "ia32_emulation=0"
    if karg_32bit not in kargs_current:
        status = status.downgrade_to(WARN)
        warnings.append(f"Missing kernel argument: {karg_32bit} (32-bit support)")

    karg_nosmt = "nosmt=force"
    if karg_nosmt not in kargs_current:
        status = status.downgrade_to(WARN)
        warnings.append(f"Missing kernel argument: {karg_nosmt} (force-disable SMT)")

    kargs_expected_unstable = (
        "amd_iommu=force_isolation",
        "debugfs=off",
        "efi=disable_early_pci_dma",
        "gather_data_sampling=force",
        "oops=panic",
    )
    for karg in kargs_expected_unstable:
        if karg not in kargs_current:
            status = status.downgrade_to(WARN)
            warnings.append(f"Missing kernel argument (unstable): {karg}")

    if status != PASS:
        rec = """To set hardened kernel arguments, run:
            $ ujust set-kargs-hardening"""

    yield Report("Checking for hardened kernel arguments", status, warnings=warnings, recs=rec)


@audit
def audit_sysctl():
    """Check for sysctl overrides."""
    sysctl_file = "/etc/sysctl.d/60-hardening.conf"
    with open(f"/usr{sysctl_file}", encoding="utf-8") as f:
        conf = f.readlines()
    sysctl_expected = parse_config(conf)
    status = PASS
    sysctl_errors = []
    with open(sysctl_file, encoding="utf-8") as f:
        etc_conf = f.readlines()
    if conf != etc_conf:
        status = WARN
        sysctl_errors.append(f"{sysctl_file} has been modified")
    for sysctl, expected in sysctl_expected.items():
        sysctl_path = f"/proc/sys/{sysctl.replace('.', '/')}"
        for path in glob.iglob(sysctl_path):
            try:
                with open(path, encoding="utf-8") as f:
                    actual = f.read().strip()
            except PermissionError:
                continue
            if not validate_sysctl(sysctl, actual, expected):
                status = FAIL
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
        status = PASS
        recs = None
    else:
        status = FAIL
        recs = """The current image is not signed.
            To rebase to a signed image, download and run or re-run install_secureblue.sh
            from the secureblue GitHub repository."""
    yield Report("Ensuring a signed image is in use", status, recs=recs)


@audit
def audit_modprobe(state):
    """Check that the kernel module blacklist has not been overridden."""
    with open("/usr/etc/modprobe.d/blacklist.conf", encoding="utf-8") as f:
        conf = f.readlines()
    blacklisted_modules = []
    for line in conf:
        words = line.strip().split()
        if words and words[0] in ["blacklist", "install"]:
            blacklisted_modules.append(words[1])
    unwanted_modules = []
    with open("/proc/modules", encoding="utf-8") as f:
        for line in f:
            mod = line.split()[0]
            if mod in blacklisted_modules:
                unwanted_modules.append(mod)
    unwanted_modules.sort()
    status = PASS
    warnings = []
    with open("/etc/modprobe.d/blacklist.conf", encoding="utf-8") as f:
        if f.readlines() != conf:
            status = WARN
            warnings.append("/etc/modprobe.d/blacklist.conf has been modified")
    for mod in unwanted_modules:
        status = FAIL
        warnings.append(f"{mod} is in blacklist.conf but it is loaded")
    state["bluetooth_loaded"] = "bluetooth" in unwanted_modules
    yield Report("Ensuring no modprobe overrides", status, warnings=warnings)


@audit
def audit_ptrace(state):
    """Ensure the ptrace syscall is forbidden."""
    with open("/proc/sys/kernel/yama/ptrace_scope", encoding="utf-8") as f:
        ptrace_scope = int(f.read())
    match ptrace_scope:
        case 3:
            status = PASS
            rec = None
        case 0:
            status = FAIL
            rec = f"""ptrace is allowed and {bold("unrestricted")} (ptrace_scope = 0)!
                For more info on what this means, see:
                https://www.kernel.org/doc/html/latest/admin-guide/LSM/Yama.html
                To forbid ptrace, run:
                $ ujust toggle-ptrace-scope
                To allow restricted ptrace, run the above command twice."""
        case _:
            status = WARN
            rec = f"""ptrace is allowed, but restricted (ptrace_scope = {ptrace_scope}).
                For more info on what this means, see:
                https://www.kernel.org/doc/html/latest/admin-guide/LSM/Yama.html
                To forbid ptrace, run:
                $ ujust toggle-ptrace-scope"""
    state["ptrace_allowed"] = status != PASS
    yield Report("Ensuring ptrace is forbidden", status, recs=rec)


@audit
def audit_authselect():
    """Ensure no authselect overrides have been made."""
    status = PASS
    cmp = filecmp.dircmp("/usr/etc/authselect", "/etc/authselect", shallow=False, ignore=[])
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        status = FAIL
    yield Report("Ensuring no authselect overrides", status)


@audit
def audit_container_policy():
    """Ensure container policy has not been modified."""
    status = PASS
    warnings = []
    policy_file = "/etc/containers/policy.json"
    if not filecmp.cmp(f"/usr{policy_file}", policy_file):
        status = FAIL
        warnings.append(f"{policy_file} has been modified")
    local_override = "~/.config/containers/policy.json"
    if os.path.isfile(os.path.expanduser(local_override)):
        status = FAIL
        warnings.append(f"{local_override} exists")
    yield Report("Ensuring no container policy overrides", status, warnings=warnings)


@audit
def audit_unconfined_userns():
    """Ensure unconfined-domain processes cannot create user namespaces."""
    if command_stdout("ujust", "check-unconfined-userns-state") == "disabled":
        status = PASS
        recs = None
    else:
        status = FAIL
        recs = """Unconfined domain user namespace creation is permitted.
                To disallow it, run:
                $ ujust toggle-unconfined-domain-userns-creation"""
    yield Report("Ensuring unconfined user namespace creation disallowed", status, recs=recs)


@audit
def audit_container_userns():
    """Ensure container-domain processes cannot create user namespaces."""
    if command_stdout("ujust", "check-container-userns-state") == "disabled":
        status = PASS
        recs = None
    else:
        status = WARN
        recs = """Container domain user namespace creation is permitted.
                To disallow it, run:
                $ ujust toggle-container-domain-userns-creation"""
    yield Report("Ensuring container user namespace creation disallowed", status, recs=recs)


@audit
def audit_usbguard():
    """Ensure usbguard is active."""
    if command_succeeds("systemctl", "is-enabled", "--quiet", "usbguard"):
        status = PASS
        warning = None
        rec = None
        if command_succeeds("systemctl", "is-failed", "--quiet", "usbguard"):
            status = status.downgrade_to(WARN)
            warning = "USBGuard is enabled but has failed to run"
    else:
        status = FAIL
        warning = "USBGuard is not enabled"
        rec = """USBGuard is not enabled. To set up USBGuard, run:
            $ ujust setup-usbguard
            Caution: if you have already set up USBGuard, this will overwrite the
            existing policy."""
    yield Report("Ensuring usbguard is active", status, warnings=warning, recs=rec)


@audit
def audit_chronyd():
    """Ensure chronyd is active."""
    if command_succeeds("systemctl", "is-enabled", "--quiet", "chronyd"):
        status = PASS
        warning = None
        rec = None
        if command_succeeds("systemctl", "is-failed", "--quiet", "chronyd"):
            status = status.downgrade_to(WARN)
            warning = "chronyd is enabled but has failed to run"
    else:
        status = FAIL
        warning = "chronyd is not enabled"
        rec = """chronyd is not enabled.
            To start and enable it, run:
            $ systemctl enable --now chronyd"""
    yield Report("Ensuring chronyd is active", status, warnings=warning, recs=rec)


@audit
def audit_dns():
    """Ensure system DNS resolution is active and secure."""
    rec = None
    warning = None
    if command_succeeds("systemctl", "is-active", "--quiet", "systemd-resolved"):
        dnssec = None
        dot = None
        conf_path = "/etc/systemd/resolved.conf.d/10-securedns.conf"
        try:
            with open(conf_path, encoding="utf-8") as f:
                config = parse_config(f)
                dnssec = config.get("DNSSEC")
                dot = config.get("DNSOverTLS")
        except FileNotFoundError:
            status = FAIL
        except PermissionError:
            status = UNKNOWN
            warning = f"Unable to read file {conf_path}"
        else:
            if dnssec == "true" and dot == "true":
                status = PASS
            elif dot == "opportunistic":
                status = WARN
            else:
                status = FAIL
        if status in (WARN, FAIL):
            caveat = " (opportunistic DNS-over-TLS only)" if dot == "opportunistic" else ""
            rec = f"""System DNS resolution is not secure{caveat}.
                    To select a secure resolver, run:
                    $ ujust dns-selector
                    If you are using a VPN, you may want to disregard this recommendation."""
    else:
        status = FAIL
        rec = """systemd-resolved is inactive.
                To start and enable it, run:
                $ systemctl enable --now systemd-resolved"""
    yield Report("Ensuring system DNS resolution is secure", status, warnings=warning, recs=rec)


@audit
def audit_mac_randomization():
    """Ensure MAC randomization is enabled."""
    status = FAIL
    warning = None
    conf_path = "/etc/NetworkManager/conf.d/rand_mac.conf"
    try:
        with open(conf_path, encoding="utf-8") as f:
            config = parse_config(f)
    except FileNotFoundError:
        pass
    except PermissionError:
        status = UNKNOWN
        warning = f"Unable to read file {conf_path}"
    else:
        ethernet = config.get("ethernet.cloned-mac-address") in ("random", "stable")
        wifi = config.get("wifi.cloned-mac-address") in ("random", "stable")
        if ethernet and wifi:
            status = PASS
    if status == FAIL:
        rec = """MAC randomization is not enabled.
                To enable it, run:
                $ ujust toggle-mac-randomization"""
    else:
        rec = None
    yield Report("Ensuring MAC randomization is enabled", status, warnings=warning, recs=rec)


@audit
def audit_rpm_ostree_timer():
    """Ensure rpm-ostree automatic updates are enabled."""
    if command_succeeds("systemctl", "is-enabled", "--quiet", "rpm-ostreed-automatic.timer"):
        status = PASS
        warning = None
        rec = None
        if command_succeeds("systemctl", "is-failed", "--quiet", "rpm-ostreed-automatic.timer"):
            status = status.downgrade_to(WARN)
            warning = "rpm-ostreed-automatic.timer is enabled but has failed to run"
    else:
        status = FAIL
        warning = "rpm-ostreed-automatic.timer is disabled"
        rec = """rpm-ostreed-automatic.timer is disabled.
                To enable, run:
                $ systemctl enable --now rpm-ostreed-automatic.timer"""
    yield Report(
        "Ensuring rpm-ostreed-automatic.timer is enabled",
        status,
        warnings=warning,
        recs=rec,
    )


@audit
def audit_podman_auto_update():
    """Ensure podman automatic updates are enabled."""
    if command_succeeds("systemctl", "is-enabled", "--quiet", "podman-auto-update.timer"):
        status = PASS
        warning = None
        rec = None
        if command_succeeds(
            "systemctl", "--user", "is-failed", "--quiet", "podman-auto-update.timer"
        ):
            status = status.downgrade_to(WARN)
            warning = "podman-auto-update.timer is enabled but has failed to run"
    else:
        status = FAIL
        warning = "podman-auto-update.timer is disabled"
        rec = """podman-auto-update.timer is disabled.
                To enable, run:
                $ systemctl enable --now podman-auto-update.timer"""
    yield Report(
        "Ensuring podman-auto-update.timer is enabled",
        status,
        warnings=warning,
        recs=rec,
    )


@audit
def audit_podman_global_auto_update():
    """Ensure podman automatic updates are enabled globally."""
    if command_succeeds(
        "systemctl", "--global", "is-enabled", "--quiet", "podman-auto-update.timer"
    ):
        status = PASS
        warning = None
        rec = None
        if command_succeeds("systemctl", "is-failed", "--quiet", "podman-auto-update.timer"):
            status = status.downgrade_to(WARN)
            warning = "podman-auto-update.timer is enabled globally but has failed to run"
    else:
        status = FAIL
        warning = "podman-auto-update.timer is not enabled globally"
        rec = """podman-auto-update.timer is not enabled globally.
                To enable, run:
                $ systemctl enable --global podman-auto-update.timer"""
    yield Report(
        "Ensuring podman-auto-update.timer is enabled globally",
        status,
        warnings=warning,
        recs=rec,
    )


@audit
def audit_flatpak_auto_update():
    """Ensure flatpak automatic updates are enabled."""
    if not command_succeeds("command", "-v", "flatpak"):
        return
    if command_succeeds(
        "systemctl", "--global", "is-enabled", "--quiet", "flatpak-user-update.timer"
    ):
        status = PASS
        warning = None
        rec = None
        if command_succeeds(
            "systemctl", "--user", "is-failed", "--quiet", "flatpak-user-update.timer"
        ):
            status = status.downgrade_to(WARN)
            warning = "flatpak-user-update.timer is enabled globally but has failed to run."
    else:
        status = FAIL
        warning = "flatpak-user-update.timer is not enabled globally"
        rec = """flatpak-user-update.timer is not enabled globally.
                To enable, run:
                $ systemctl enable --global flatpak-user-update.timer"""
    yield Report(
        "Ensuring flatpak-user-update.timer is enabled globally",
        status,
        warnings=warning,
        recs=rec,
    )

    if command_succeeds("systemctl", "is-enabled", "--quiet", "flatpak-system-update.timer"):
        status = PASS
        warning = None
        rec = None
        if command_succeeds("systemctl", "is-failed", "--quiet", "flatpak-system-update.timer"):
            status = status.downgrade_to(WARN)
            warning = "flatpak-system-update.timer is enabled but has failed to run."
    else:
        status = FAIL
        warning = "flatpak-system-update.timer is not enabled"
        rec = """flatpak-system-update.timer is not enabled.
                To enable, run:
                $ systemctl enable --now flatpak-system-update.timer"""
    yield Report(
        "Ensuring flatpak-system-update.timer is enabled",
        status,
        warnings=warning,
        recs=rec,
    )


@audit
def audit_wheel():
    """Ensure the current user is not in the wheel group."""
    if "wheel" in command_stdout("groups").split():
        rec = f"""Current user is in the wheel group.
            To set up a separate wheel account, follow the instructions here:
            {bold("https://secureblue.dev/install#wheel")}"""
        status = FAIL
    else:
        rec = None
        status = PASS
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
        status = PASS
        rec = None
    else:
        status = FAIL
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
        "command",
        "-p",
        "gsettings",
        "get",
        "org.gnome.shell",
        "allow-extension-installation",
    )
    if allowed == "false":
        status = PASS
        rec = None
    else:
        status = FAIL
        rec = """GNOME user extensions are enabled. To disable, run:
            $ ujust toggle-gnome-extensions"""
    yield Report("Ensuring GNOME user extensions are disabled", status, recs=rec)


@audit
def audit_selinux():
    """Ensure SELinux is in enforcing mode."""
    if command_stdout("getenforce") == "Enforcing":
        status = PASS
        rec = None
    else:
        status = FAIL
        rec = """SELinux is in Permissive mode.
            To set to Enforcing mode, run:
            $ run0 setenforce 1"""
    yield Report("Ensuring SELinux is in Enforcing mode", status, recs=rec)


@audit
def audit_environment_file():
    """Ensure /etc/environment has not been modified."""
    env_file = "/etc/environment"
    status = PASS
    warning = None
    rec = None
    try:
        if not filecmp.cmp("/usr" + env_file, env_file):
            status = WARN
            warning = f"{env_file} has been modified"
    except FileNotFoundError:
        status = WARN
        warning = f"{env_file} has been deleted"
    except PermissionError:
        status = WARN
        warning = f"{env_file} cannot be read"
    if status != PASS:
        rec = f"""{env_file} has been modified. To reset it, run:
            $ run0 cp -p /usr{env_file} {env_file}"""
    yield Report("Ensuring no environment file overrides", status, warnings=warning, recs=rec)


@audit
@depends_on("audit_signed_image")
def audit_kde_ghns(state):
    """Ensure KDE GHNS is disabled."""
    if state["image"] != Image.KINOITE:
        return
    status = FAIL
    warning = None
    try:
        with open("/etc/xdg/kdeglobals", encoding="utf-8") as f:
            config = parse_config(f)
    except (FileNotFoundError, PermissionError):
        status = WARN
        warning = "/etc/xdg/kdeglobals not found or inaccessible"
    else:
        if config.get("ghns") == "false":
            status = PASS
    if status == FAIL:
        rec = """KDE GHNS is enabled.
            To disable, run:
            $ ujust toggle-ghns"""
    else:
        rec = None
    yield Report("Ensuring KDE GHNS is disabled", status, warnings=warning, recs=rec)


@audit
def audit_ld_preload():
    """Ensure ld.so.preload exists and is readable only by root."""
    status = PASS
    warnings = []
    rec = None
    ld_so_preload = "/etc/ld.so.preload"
    try:
        stat_result = os.stat(ld_so_preload)
    except FileNotFoundError:
        status = FAIL
        warnings.append(f"{ld_so_preload} not found")
    else:
        mode = stat.S_IMODE(stat_result.st_mode)
        expected_mode = 0o600
        if mode != expected_mode:
            status = WARN
            warnings.append(f"{ld_so_preload} has mode {mode:o} (expected {expected_mode:o})")
        if stat_result.st_uid != 0:
            status = FAIL
            warnings.append(f"{ld_so_preload} is owned by a non-root user!")
    if status != PASS:
        rec = f"""{ld_so_preload} has been modified or deleted.
            To reset it and enable hardened_malloc for system processes, run:
            $ run0 cp -p /usr{ld_so_preload} {ld_so_preload}"""
    yield Report(
        "Ensuring ld.so.preload has expected permissions",
        status,
        warnings=warnings,
        recs=rec,
    )


@audit
def audit_hardened_malloc():
    """Ensure hardened_malloc is set to be preloaded in place of the default system malloc."""
    rec = None
    ld_preload = os.environ.get("LD_PRELOAD")
    preloads = [] if ld_preload is None else ld_preload.split()
    if preloads == ["libhardened_malloc.so"]:
        status = PASS
        warning = None
    elif "libhardened_malloc.so" in preloads:
        status = WARN
        warning = "hardened_malloc set, but LD_PRELOAD has been modified"
    elif "libhardened_malloc-light.so" in preloads:
        status = WARN
        warning = "'light' variant of hardened_malloc set"
    elif "libhardened_malloc-pkey.so" in preloads:
        status = WARN
        warning = "'pkey' variant of hardened_malloc set"
    else:
        status = FAIL
        warning = "libhardened_malloc not set in LD_PRELOAD"

    if status != PASS:
        rec = """The LD_PRELOAD environment variable has been modified or is unset.
            Check that LD_PRELOAD=libhardened_malloc.so has not been overridden in
            /etc/profile.d or related configuration files."""
    yield Report(
        "Ensuring hardened_malloc is set to be preloaded",
        status,
        warnings=warning,
        recs=rec,
    )


@audit
def audit_secureboot():
    """Ensure secureboot is enabled."""
    if command_stdout("mokutil", "--sb-state", check=False) == "SecureBoot enabled":
        status = PASS
    else:
        status = FAIL
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
        if not os.path.exists(path) or (not os.path.isfile(path) and not os.path.isdir(path)):
            unlocked_files.append(path)
        else:
            try:
                immutable = "i" in command_stdout("lsattr", "-d", path).split()[0]
            except subprocess.CalledProcessError:
                immutable = False
            if not immutable:
                unlocked_files.append(path)
    if unlocked_files:
        status = FAIL
        unlocked_files_string = "\n".join(unlocked_files)
        rec = f"""Bash environment is not locked down.
                The following files do not appear to be immutable or do not exist:
                {unlocked_files_string}
                To fix, run:
                $ ujust toggle-bash-environment-lockdown"""
    else:
        status = PASS
        rec = None
    yield Report("Ensuring current user's bash environment is locked down", status, recs=rec)


@audit
@categorize("flatpak")
def audit_flatpak_remotes():
    """Audit flatpak remotes."""
    if not command_succeeds("command", "-v", "flatpak"):
        return

    remotes = command_stdout("flatpak", "remotes", "--columns=name,url,subset").splitlines()
    for remote in remotes:
        if not remote:
            continue
        name, url, subset = remote.split("\t")
        warnings = []
        if url not in [
            "https://dl.flathub.org/repo/",
            "https://dl.flathub.org/beta-repo/",
        ]:
            status = FAIL
            warnings.append(f"{name} is configured with an unknown url")
        elif subset != "verified":
            status = FAIL
            warnings.append(f"{name} is not a verified repo")
        else:
            status = PASS
        yield Report(f"Auditing flatpak remote {name}", status, warnings=warnings)


@audit
@categorize("flatpak")
@depends_on("audit_modprobe", "audit_ptrace")
async def audit_flatpak_permissions(state):
    """Audit flatpak permissions."""
    if not command_succeeds("command", "-v", "flatpak"):
        return

    flatpaks = []
    for line in command_stdout(
        "flatpak", "list", "--app", "--columns=application,branch"
    ).splitlines():
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
        flatpak_permissions_state = check_flatpak_permissions(
            name, perms, state["bluetooth_loaded"], state["ptrace_allowed"]
        )
        report_text = f"Auditing {name}" if version == "stable" else f"Auditing {name} ({version})"
        yield Report(
            report_text,
            flatpak_permissions_state.status,
            warnings=flatpak_permissions_state.warnings,
            recs=flatpak_permissions_state.recs,
        )


###############################################################################
# Checks to be run go above this line.
###############################################################################


def handle_sigint(_sig, _frame):
    """Gracefully handle interrupt signal."""
    print_err("\n[Audit process interrupted. Exiting.]")
    # Suppress output from exceptions in unfinished tasks
    sys.stderr = None
    sys.exit(1)


async def main() -> int:
    """Main entry point. Parse command-line arguments and run audit."""
    signal.signal(signal.SIGINT, handle_sigint)
    warn_if_root()
    parser = argparse.ArgumentParser(
        prog="ujust audit-secureblue",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Audit secureblue configuration for security",
        epilog=get_legend(),
    )
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
