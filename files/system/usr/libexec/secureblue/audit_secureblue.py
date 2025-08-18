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
from auditor import (
    Report,
    Status,
    audit,
    bold,
    categorize,
    depends_on,
    gettext_marker,
    global_audit,
)
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

_: Final = gettext_marker()

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
            warnings.append(_("Missing kernel argument: {0}").format(karg))

    karg_32bit = "ia32_emulation=0"
    if karg_32bit not in kargs_current:
        status = status.downgrade_to(WARN)
        warnings.append(_("Missing kernel argument: {0} (32-bit support)").format(karg_32bit))

    karg_nosmt = "nosmt=force"
    if karg_nosmt not in kargs_current:
        status = status.downgrade_to(WARN)
        warnings.append(_("Missing kernel argument: {0} (force-disable SMT)").format(karg_nosmt))

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
            warnings.append(_("Missing kernel argument (unstable): {0}").format(karg))

    if status != PASS:
        rec = _("To set hardened kernel arguments, run:") + "\n$ ujust set-kargs-hardening"

    yield Report(_("Checking for hardened kernel arguments"), status, warnings=warnings, recs=rec)


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
        sysctl_errors.append(_("The file {0} has been modified.").format(sysctl_file))
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
                sysctl_errors.append(
                    _("{0} should be {1}, but is actually {2}.").format(sysctl, expected, actual)
                )
                break
    yield Report(_("Ensuring no sysctl overrides"), status, warnings=sysctl_errors)


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
        recs = _("""The current image is not signed.
            To rebase to a signed image, download and run or re-run {0}
            from the secureblue GitHub repository.""").format("install_secureblue.sh")
    yield Report(_("Ensuring a signed image is in use"), status, recs=recs)


@audit
def audit_modprobe(state):
    """Check that the kernel module blacklist has not been overridden."""
    blacklist_file = "/etc/modprobe.d/blacklist.conf"
    with open(f"/usr{blacklist_file}", encoding="utf-8") as f:
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
    with open(blacklist_file, encoding="utf-8") as f:
        if f.readlines() != conf:
            status = WARN
            warnings.append(_("The file {0} has been modified.").format(blacklist_file))
    for mod in unwanted_modules:
        status = FAIL
        warnings.append(
            _("The module {0} is in {1}, but it is loaded.").format(mod, blacklist_file)
        )
    state["bluetooth_loaded"] = "bluetooth" in unwanted_modules
    yield Report(_("Ensuring no modprobe overrides"), status, warnings=warnings)


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
            rec_lines = (
                _("ptrace is allowed and **unrestricted** ({0})!").format("ptrace_scope = 0"),
                _("For more info on what this means, see:"),
                "https://www.kernel.org/doc/html/latest/admin-guide/LSM/Yama.html",
                _("To forbid ptrace, run:"),
                "$ ujust toggle-ptrace-scope",
                _("To allow restricted ptrace, run the above command twice."),
            )
            rec = "\n".join(rec_lines)
        case _:
            status = WARN
            rec_lines = (
                _("ptrace is allowed, but restricted ({0}).").format(
                    f"ptrace_scope = {ptrace_scope}"
                ),
                _("For more info on what this means, see:"),
                "https://www.kernel.org/doc/html/latest/admin-guide/LSM/Yama.html",
                _("To forbid ptrace, run:"),
                "$ ujust toggle-ptrace-scope",
            )
            rec = "\n".join(rec_lines)
    state["ptrace_allowed"] = status != PASS
    yield Report(_("Ensuring ptrace is forbidden"), status, recs=rec)


@audit
def audit_authselect():
    """Ensure no authselect overrides have been made."""
    status = PASS
    cmp = filecmp.dircmp("/usr/etc/authselect", "/etc/authselect", shallow=False, ignore=[])
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        status = FAIL
    yield Report(_("Ensuring no authselect overrides"), status)


@audit
def audit_container_policy():
    """Ensure container policy has not been modified."""
    status = PASS
    warnings = []
    policy_file = "/etc/containers/policy.json"
    if not filecmp.cmp(f"/usr{policy_file}", policy_file):
        status = FAIL
        warnings.append(_("The file {0} has been modified.").format(policy_file))
    local_override = "~/.config/containers/policy.json"
    if os.path.isfile(os.path.expanduser(local_override)):
        status = FAIL
        warnings.append(_("{0} exists.").format(local_override))
    yield Report(_("Ensuring no container policy overrides"), status, warnings=warnings)


@audit
def audit_unconfined_userns():
    """Ensure unconfined-domain processes cannot create user namespaces."""
    if command_stdout("ujust", "check-unconfined-userns-state") == "disabled":
        status = PASS
        recs = None
    else:
        status = FAIL
        rec_lines = (
            _("Unconfined domain user namespace creation is permitted."),
            _("To disallow it, run:"),
            "$ ujust toggle-unconfined-domain-userns-creation",
        )
        recs = "\n".join(rec_lines)
    yield Report(_("Ensuring unconfined user namespace creation disallowed"), status, recs=recs)


@audit
def audit_container_userns():
    """Ensure container-domain processes cannot create user namespaces."""
    if command_stdout("ujust", "check-container-userns-state") == "disabled":
        status = PASS
        recs = None
    else:
        status = WARN
        rec_lines = (
            _("Container domain user namespace creation is permitted."),
            _("To disallow it, run:"),
            "$ ujust toggle-container-domain-userns-creation",
        )
        recs = "\n".join(rec_lines)
    yield Report(_("Ensuring container user namespace creation disallowed"), status, recs=recs)


@audit
def audit_usbguard():
    """Ensure usbguard is active."""
    if command_succeeds("systemctl", "is-enabled", "--quiet", "usbguard"):
        status = PASS
        warning = None
        rec = None
        if command_succeeds("systemctl", "is-failed", "--quiet", "usbguard"):
            status = status.downgrade_to(WARN)
            warning = _("USBGuard is enabled but has failed to run.")
    else:
        status = FAIL
        warning = _("USBGuard is not enabled.")
        rec_lines = (
            warning,
            _("To set up USBGuard, run:"),
            "$ ujust setup-usbguard",
            _(
                "Caution: if you have already set up USBGuard, this will overwrite the existing policy."
            ),
        )
        rec = "\n".join(rec_lines)
    yield Report(_("Ensuring USBGuard is active"), status, warnings=warning, recs=rec)


@audit
def audit_chronyd():
    """Ensure chronyd is active."""
    if command_succeeds("systemctl", "is-enabled", "--quiet", "chronyd"):
        status = PASS
        warning = None
        rec = None
        if command_succeeds("systemctl", "is-failed", "--quiet", "chronyd"):
            status = status.downgrade_to(WARN)
            warning = _("{0} is enabled but has failed to run.").format("chronyd")
    else:
        status = FAIL
        warning = _("{0} is not enabled.").format("chronyd")
        rec_lines = (warning, _("To start and enable it, run:"), "$ systemctl enable --now chronyd")
        rec = "\n".join(rec_lines)
    yield Report(_("Ensuring chronyd is active"), status, warnings=warning, recs=rec)


@audit
def audit_dns():
    """Ensure system DNS resolution is active and secure."""
    rec = None
    warning = None
    if command_succeeds("systemctl", "is-active", "--quiet", "systemd-resolved"):
        dnssec = None
        dot = None
        conf_path = "/etc/systemd/resolved.conf.d/10-securedns.conf"
        fail_msg = _("System DNS resolution is not secure.")
        try:
            with open(conf_path, encoding="utf-8") as f:
                config = parse_config(f)
                dnssec = config.get("DNSSEC")
                dot = config.get("DNSOverTLS")
        except FileNotFoundError:
            status = FAIL
        except PermissionError:
            status = UNKNOWN
            warning = _("Unable to read file {0}.").format(conf_path)
        else:
            if dnssec == "true" and dot == "true":
                status = PASS
            elif dot == "opportunistic":
                status = WARN
                fail_msg = _(
                    "System DNS resolution is not secure (opportunistic DNS-over-TLS only)."
                )
            else:
                status = FAIL
        if status in (WARN, FAIL):
            rec_lines = (
                fail_msg,
                _("To select a secure resolver, run:"),
                "$ ujust dns-selector",
                _("If you are using a VPN, you may want to disregard this recommendation."),
            )
            rec = "\n".join(rec_lines)
    else:
        status = FAIL
        rec_lines = (
            _("{0} is inactive.").format("systemd-resolved"),
            _("To start and enable it, run:"),
            "$ systemctl enable --now systemd-resolved",
        )
        rec = "\n".join(rec_lines)
    yield Report(_("Ensuring system DNS resolution is secure"), status, warnings=warning, recs=rec)


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
        warning = _("Unable to read file {0}.").format(conf_path)
    else:
        ethernet = config.get("ethernet.cloned-mac-address") in ("random", "stable")
        wifi = config.get("wifi.cloned-mac-address") in ("random", "stable")
        if ethernet and wifi:
            status = PASS
    if status == FAIL:
        rec_lines = (
            _("MAC randomization is not enabled."),
            _("To enable it, run:"),
            "$ ujust toggle-mac-randomization",
        )
        rec = "\n".join(rec_lines)
    else:
        rec = None
    yield Report(_("Ensuring MAC randomization is enabled"), status, warnings=warning, recs=rec)


@audit
def audit_rpm_ostree_timer():
    """Ensure rpm-ostree automatic updates are enabled."""
    if command_succeeds("systemctl", "is-enabled", "--quiet", "rpm-ostreed-automatic.timer"):
        status = PASS
        warning = None
        rec = None
        if command_succeeds("systemctl", "is-failed", "--quiet", "rpm-ostreed-automatic.timer"):
            status = status.downgrade_to(WARN)
            warning = _("{0} is enabled but has failed to run.").format(
                "rpm-ostreed-automatic.timer"
            )
    else:
        status = FAIL
        warning = _("{0} is disabled.").format("rpm-ostreed-automatic.timer")
        rec_lines = (
            warning,
            _("To enable it, run:"),
            "$ systemctl enable --now rpm-ostreed-automatic.timer",
        )
        rec = "\n".join(rec_lines)
    yield Report(
        _("Ensuring {0} is enabled").format("rpm-ostreed-automatic.timer"),
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
            warning = _("{0} is enabled but has failed to run.").format("podman-auto-update.timer")
    else:
        status = FAIL
        warning = _("{0} is disabled.").format("podman-auto-update.timer")
        rec_lines = (
            warning,
            _("To enable it, run:"),
            "$ systemctl enable --now podman-auto-update.timer",
        )
        rec = "\n".join(rec_lines)
    yield Report(
        _("Ensuring {0} is enabled").format("podman-auto-update.timer"),
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
            warning = _("{0} is enabled globally but has failed to run.").format(
                "podman-auto-update.timer"
            )
    else:
        status = FAIL
        warning = _("{0} is not enabled globally.").format("podman-auto-update.timer")
        rec_lines = (
            warning,
            _("To enable it, run:"),
            "$ systemctl enable --global podman-auto-update.timer",
        )
        rec = "\n".join(rec_lines)
    yield Report(
        _("Ensuring {0} is enabled globally").format("podman-auto-update.timer"),
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
            warning = _("{0} is enabled globally but has failed to run.").format(
                "flatpak-user-update.timer"
            )
    else:
        status = FAIL
        warning = _("{0} is not enabled globally.").format("flatpak-user-update.timer")
        rec_lines = (
            warning,
            _("To enable it, run:"),
            "$ systemctl enable --global flatpak-user-update.timer",
        )
        rec = "\n".join(rec_lines)
    yield Report(
        _("Ensuring {0} is enabled globally").format("flatpak-user-update.timer"),
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
            warning = _("{0} is enabled but has failed to run.").format(
                "flatpak-system-update.timer"
            )
    else:
        status = FAIL
        warning = _("{0} is not enabled.").format("flatpak-system-update.timer")
        rec_lines = (
            warning,
            _("To enable it, run:"),
            "$ systemctl enable --now flatpak-system-update.timer",
        )
        rec = "\n".join(rec_lines)
    yield Report(
        _("Ensuring {0} is enabled").format("flatpak-system-update.timer"),
        status,
        warnings=warning,
        recs=rec,
    )


@audit
def audit_wheel():
    """Ensure the current user is not in the wheel group."""
    if "wheel" in command_stdout("groups").split():
        rec_lines = (
            _("The current user is in the wheel group."),
            _("To set up a separate wheel account, follow the instructions here:"),
            bold("https://secureblue.dev/post-install#wheel"),
        )
        rec = "\n".join(rec_lines)
        status = FAIL
    else:
        rec = None
        status = PASS
    yield Report(_("Ensuring user is not a member of the wheel group"), status, recs=rec)


@audit
@depends_on("audit_signed_image")
def audit_xwayland(state):
    """Check whether xwayland is disabled."""
    match state["image"]:
        case Image.SILVERBLUE:
            de = _("GNOME")
            path = "/etc/systemd/user/org.gnome.Shell@wayland.service.d/override.conf"
        case Image.KINOITE:
            de = _("KDE Plasma")
            path = "/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf"
        case Image.SERICEA:
            de = _("Sway")
            path = "/etc/sway/config.d/99-noxwayland.conf"
        case _:
            return
    if os.path.isfile(path):
        status = PASS
        rec = None
    else:
        status = FAIL
        rec_lines = (
            _("Xwayland is enabled for {0}.").format(de),
            _("To disable it, run:"),
            "$ ujust toggle-xwayland",
        )
        rec = "\n".join(rec_lines)
    yield Report(_("Ensuring {0} is disabled for {1}").format("Xwayland", de), status, recs=rec)


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
        rec_lines = (
            _("GNOME user extensions are enabled."),
            _("To disable this, run:"),
            "$ ujust toggle-gnome-extensions",
        )
        rec = "\n".join(rec_lines)
    yield Report(_("Ensuring GNOME user extensions are disabled"), status, recs=rec)


@audit
def audit_selinux():
    """Ensure SELinux is in enforcing mode."""
    if command_stdout("getenforce") == "Enforcing":
        status = PASS
        rec = None
    else:
        status = FAIL
        rec_lines = (
            _("SELinux is in Permissive mode."),
            _("To set it to Enforcing mode, run:"),
            "$ run0 setenforce 1",
        )
        rec = "\n".join(rec_lines)
    yield Report(_("Ensuring SELinux is in Enforcing mode"), status, recs=rec)


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
            warning = _("The file {0} has been modified.").format(env_file)
    except FileNotFoundError:
        status = WARN
        warning = _("The file {0} has been deleted.").format(env_file)
    except PermissionError:
        status = WARN
        warning = _("The file {0} cannot be read.").format(env_file)
    if status != PASS:
        rec_lines = (
            _("The file {0} has been modified."),
            _("To reset it, run:"),
            f"$ run0 cp -p /usr{env_file} {env_file}",
        )
        rec = "\n".join(rec_lines)
    yield Report(_("Ensuring no environment file overrides"), status, warnings=warning, recs=rec)


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
        warning = _("The file {0} was not found or inaccessible.").format("/etc/xdg/kdeglobals")
    else:
        if config.get("ghns") == "false":
            status = PASS
    if status == FAIL:
        rec_lines = (
            _("KDE GNHS is enabled."),
            _("To disable it, run:"),
            "$ ujust toggle-ghns",
        )
        rec = "\n".join(rec_lines)
    else:
        rec = None
    yield Report(_("Ensuring KDE GHNS is disabled"), status, warnings=warning, recs=rec)


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
        warnings.append(_("The file {0} was not found.").format(ld_so_preload))
    else:
        mode = stat.S_IMODE(stat_result.st_mode)
        expected_mode = 0o600
        if mode != expected_mode:
            status = WARN
            warnings.append(
                _("{0} has mode {1:o} (expected {2:o})").format(ld_so_preload, mode, expected_mode)
            )
        if stat_result.st_uid != 0:
            status = FAIL
            warnings.append(_("{0} is owned by a non-root user!").format(ld_so_preload))
    if status != PASS:
        rec_lines = (
            _("The file {0} has been modified or deleted.").format(ld_so_preload),
            _("To reset it and enable hardened_malloc for system processes, run:"),
            f"$ run0 cp -p /usr{ld_so_preload} {ld_so_preload}",
        )
        rec = "\n".join(rec_lines)
    yield Report(
        _("Ensuring {0} has expected permissions").format("ld.so.preload"),
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
        warning = _("{0} is set, but {1} has been modified.").format(
            "hardened_malloc", "LD_PRELOAD"
        )
    elif "libhardened_malloc-light.so" in preloads:
        status = WARN
        warning = _("The '{0}' variant of {1} has been set.").format("light", "hardened_malloc")
    elif "libhardened_malloc-pkey.so" in preloads:
        status = WARN
        warning = _("The '{0}' variant of {1} has been set.").format("pkey", "hardened_malloc")
    else:
        status = FAIL
        warning = _("{0} has not been set.").format("LD_PRELOAD=libhardened_malloc.so")

    if status != PASS:
        rec = _("""The environment variable {0} has been modified or is unset.
                Check that {1} has not been overridden in
                {2} or related configuration files.""").format(
            "LD_PRELOAD", "LD_PRELOAD=libhardened_malloc.so", "/etc/profile.d"
        )
    yield Report(
        _("Ensuring hardened_malloc is set to be preloaded"),
        status,
        warnings=warning,
        recs=rec,
    )


@audit
def audit_secureboot():
    """Ensure secureboot is enabled."""
    sb_enabled = command_stdout("mokutil", "--sb-state", check=False) == "SecureBoot enabled"
    status = PASS if sb_enabled else FAIL
    yield Report(_("Ensuring secure boot is enabled"), status)


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
        rec_lines = (
            _("Bash environment is not locked down."),
            _("The following files do not appear to be immutable or do not exist:"),
            *unlocked_files,
            _("To fix this, run:"),
            "$ ujust toggle-bash-environment-lockdown",
        )
        rec = "\n".join(rec_lines)
    else:
        status = PASS
        rec = None
    yield Report(_("Ensuring current user's bash environment is locked down"), status, recs=rec)


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
            warnings.append(_("{0} is configured with an unknown URL.").format(name))
        elif subset != "verified":
            status = FAIL
            warnings.append(_("{0} is not a verified flatpak repository.").format(name))
        else:
            status = PASS
        yield Report(_("Auditing flatpak remote {0}").format(name), status, warnings=warnings)


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
        display_name = name if version == "stable" else f"{name} ({version})"
        report_text = _("Auditing {0}").format(display_name)
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
    print_err("\n" + _("[Audit process interrupted. Exiting.]"))
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
        description=_("Audit secureblue configuration for security"),
        epilog=get_legend(),
    )
    categories = ",".join(sorted(global_audit.categories))
    parser.add_argument("-s", "--skip", default="", help=_("skip categories") + f" ({categories})")
    parser.add_argument("-j", "--json", action="store_true", help=_("display output as JSON"))
    args = parser.parse_args()
    skip = args.skip.split(",") if args.skip else []
    if any(cat not in global_audit.categories for cat in skip):
        print(_("Valid arguments to {0} are: {1}").format("--skip", categories), file=sys.stderr)
        sys.exit(1)
    error_occurred = False
    if args.json:
        async for report_json in global_audit.run_json(exclude=skip):
            print(report_json)
        return 0
    async for check, err in global_audit.run(exclude=skip, width=get_width()):
        print_err("\n" + _("*** Error in check '{0}' ***").format(check.name))
        traceback.print_exception(err)
        print_err("\n" + _("*** Continuing... ***"))
        error_occurred = True
    if "flatpak" not in skip and command_succeeds("command", "-v", "flatpak"):
        print(_("Use option '{0}' to skip flatpak recommendations.").format(bold("--skip flatpak")))
    warn_if_root()
    if error_occurred:
        print_err("\n" + _("*** WARNING: Unexpected error occurred. ***"))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
