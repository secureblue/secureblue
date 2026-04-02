#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Auditing script for secureblue. See https://secureblue.dev/ for more info.
"""

import argparse
import asyncio
import configparser
import filecmp
import getpass
import glob
import os
import os.path
import signal
import stat

# All subprocess calls we make have trusted inputs and do not use shell=True.
import subprocess
import sys
import traceback
from typing import Final

import kargs_hardening_common
from audit_flatpak import check_flatpak_permissions, parse_flatpak_permissions
from audit_utils import (
    analyze_active_container_policy,
    get_flatpak_permissions,
    get_legend,
    get_width,
    normalize_sysctl,
    validate_sysctl,
    warn_if_root,
)
from auditor import (
    Note,
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
    booted_image_ref,
    command_stdout,
    command_succeeds,
    is_module_loaded,
    is_using_vpn,
    loaded_kernel_modules,
    parse_config,
    print_err,
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
    notes = []
    rec = None

    kargs_current = frozenset(command_stdout("rpm-ostree", "kargs").split())
    kargs_expected = kargs_hardening_common.DEFAULT_KARGS
    for karg in kargs_expected:
        if karg not in kargs_current:
            status = status.downgrade_to(FAIL)
            notes.append(Note(_("Missing kernel argument: {0}").format(karg), FAIL))

    karg_32bit = kargs_hardening_common.DISABLE_32_BIT
    if karg_32bit not in kargs_current:
        status = status.downgrade_to(WARN)
        notes.append(
            Note(_("Missing kernel argument: {0} (32-bit support)").format(karg_32bit), WARN)
        )

    karg_nosmt = kargs_hardening_common.FORCE_NOSMT
    if karg_nosmt not in kargs_current:
        status = status.downgrade_to(WARN)
        notes.append(
            Note(_("Missing kernel argument: {0} (force-disable SMT)").format(karg_nosmt), WARN)
        )

    kargs_expected_unstable = kargs_hardening_common.UNSTABLE_KARGS
    for karg in kargs_expected_unstable:
        if karg not in kargs_current:
            status = status.downgrade_to(WARN)
            notes.append(Note(_("Missing kernel argument (unstable): {0}").format(karg), WARN))

    if status != PASS:
        rec = _("To set hardened kernel arguments, run:") + "\n$ ujust set-kargs-hardening"

    yield Report(_("Checking for hardened kernel arguments"), status, notes=notes, recs=rec)


@audit
def audit_sysctl():
    """Check for sysctl overrides."""
    sysctl_file = "/usr/lib/sysctl.d/55-hardening.conf"
    with open(sysctl_file, encoding="utf-8") as f:
        conf = f.readlines()
    sysctl_expected = parse_config(conf)
    status = PASS
    notes = []
    for sysctl, expected in sysctl_expected.items():
        sysctl_path = f"/proc/sys/{sysctl.replace('.', '/')}"
        for path in glob.iglob(sysctl_path):
            try:
                with open(path, encoding="utf-8") as f:
                    actual = normalize_sysctl(f.read())
            except PermissionError:
                continue
            if sysctl == "kernel.printk" and actual == "15 3 3 3":
                status = WARN
                note_lines = [
                    _("{0} should be {1}, but is actually {2}.").format(sysctl, expected, actual),
                    _("This is likely due to a kernel fault, as documented in `{0}`.").format(
                        "man 2 syslog"
                    ),
                ]
                notes.append(Note("\n".join(note_lines), WARN))
                break
            if not validate_sysctl(sysctl, actual, expected):
                status = FAIL
                notes.append(
                    Note(
                        _("{0} should be {1}, but is actually {2}.").format(
                            sysctl, expected, actual
                        ),
                        FAIL,
                    )
                )
                break
    yield Report(_("Ensuring no sysctl overrides"), status, notes=notes)


@audit
def audit_signed_image(state):
    """Check that the secureblue image is signed."""
    image_ref = booted_image_ref()
    state["image"] = Image.from_image_ref(image_ref)
    if image_ref.startswith("ostree-image-signed:"):
        status = PASS
        rec = None
    else:
        status = FAIL
        image_ref_no_prefix = image_ref.removeprefix("ostree-unverified-registry:")
        image_ref_no_prefix = image_ref_no_prefix.removeprefix("docker://")
        signed_image_ref = f"ostree-image-signed:docker://{image_ref_no_prefix}"
        rec = "\n".join(
            [
                _("The current image is not signed."),
                _("To rebase to a signed image, run the following command:"),
                f"$ rpm-ostree rebase {signed_image_ref}",
            ]
        )
    yield Report(_("Ensuring a signed image is in use"), status, recs=rec)


@audit
def audit_modprobe(state):
    """Check for modprobe overrides."""
    modprobe_dir = "/usr/lib/modprobe.d"
    modprobe_files = ("secureblue.conf", "secureblue-framebuffer.conf")
    blocked_modules = []
    for file in modprobe_files:
        with open(f"{modprobe_dir}/{file}", encoding="utf-8") as f:
            conf = f.readlines()
        for line in conf:
            words = line.strip().split(maxsplit=2)
            if words and words[0] in ("blacklist", "install"):
                blocked_modules.append(words[1])
    unwanted_modules = []
    loaded_modules = loaded_kernel_modules()
    unwanted_modules = [mod for mod in blocked_modules if mod in loaded_modules]
    unwanted_modules.sort()
    status = PASS
    notes = []
    for mod in unwanted_modules:
        status = FAIL
        notes.append(
            Note(
                _("The module {0} is blocked in {1}, but has been loaded anyway.").format(
                    mod, modprobe_dir
                ),
                FAIL,
            )
        )
    state["bluetooth_loaded"] = "bluetooth" in unwanted_modules
    yield Report(_("Ensuring no modprobe overrides"), status, notes=notes)


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
            rec_lines = [
                _("ptrace is allowed and **unrestricted** ({0})!").format("ptrace_scope = 0"),
                _("For more info on what this means, see:"),
                "https://www.kernel.org/doc/html/latest/admin-guide/LSM/Yama.html",
                _("To forbid ptrace, run:"),
                "$ ujust toggle-ptrace-scope",
                _("To allow restricted ptrace, run the above command twice."),
            ]
            rec = "\n".join(rec_lines)
        case _:
            status = WARN
            rec_lines = [
                _("ptrace is allowed, but restricted ({0}).").format(
                    f"ptrace_scope = {ptrace_scope}"
                ),
                _("For more info on what this means, see:"),
                "https://www.kernel.org/doc/html/latest/admin-guide/LSM/Yama.html",
                _("To forbid ptrace, run:"),
                "$ ujust toggle-ptrace-scope",
            ]
            rec = "\n".join(rec_lines)
    state["ptrace_allowed"] = status != PASS
    yield Report(_("Ensuring ptrace is forbidden"), status, recs=rec)


@audit
def audit_container_policy():
    """Check for modifications to container policy."""
    status = PASS
    notes = []
    system_policy_file = "/etc/containers/policy.json"
    if not filecmp.cmp(f"/usr{system_policy_file}", system_policy_file):
        status = status.downgrade_to(INFO)
        notes.append(Note(_("The file {0} has been modified.").format(system_policy_file), INFO))

    policy_audit, policy_path = analyze_active_container_policy()

    if policy_path != str(system_policy_file):
        status = status.downgrade_to(INFO)
        notes.append(
            Note(_("Container policy has a local override at {0}.").format(policy_path), INFO)
        )
    elif status == PASS:
        # No need to parse the policy, it's unmodified.
        yield Report(_("Analyzing container policy"), PASS)
        return

    if not policy_audit.default_secure:
        status = status.downgrade_to(FAIL)
        notes.append(Note(_("The default container policy is insecure."), FAIL))

    insecure_scopes = []

    for transport_name, transport_policy in policy_audit.transports.items():
        if not transport_policy.default_secure:
            status = status.downgrade_to(FAIL)
            notes.append(
                Note(
                    _("The default container policy for transport '{0}' is insecure.").format(
                        transport_name
                    ),
                    FAIL,
                )
            )

        insecure_scopes += [
            f"{transport_name}:{scope}" for scope in transport_policy.insecure_scopes
        ]

    if insecure_scopes:
        status = status.downgrade_to(WARN)
        notes.append(
            Note(
                _(
                    "Signature validation is disabled for containers at the following scopes:\n{0}"
                ).format("\n".join(insecure_scopes)),
                WARN,
            )
        )

    yield Report(_("Analyzing container policy"), status, notes=notes)


@audit
def audit_unconfined_userns():
    """Ensure unconfined-domain processes cannot create user namespaces."""
    if command_stdout("ujust", "set-unconfined-userns", "status") == "disabled":
        status = PASS
        recs = None
    else:
        status = FAIL
        rec_lines = [
            _("Unconfined domain user namespace creation is permitted."),
            _("To disallow it, run:"),
            "$ ujust set-unconfined-userns off",
        ]
        recs = "\n".join(rec_lines)
    yield Report(_("Ensuring unconfined user namespace creation disallowed"), status, recs=recs)


@audit
def audit_container_userns(state):
    """Ensure container-domain processes cannot create user namespaces."""
    status = PASS
    recs = None
    container_userns = command_stdout("ujust", "set-container-userns", "status") != "disabled"
    state["container_userns_enabled"] = container_userns
    if container_userns:
        status = WARN
        rec_lines = [
            _("Container domain user namespace creation is permitted."),
            _("To disallow it, run:"),
            "$ ujust set-container-userns off",
        ]
        recs = "\n".join(rec_lines)
    yield Report(_("Ensuring container user namespace creation disallowed"), status, recs=recs)


@audit
def audit_usbguard():
    """Ensure usbguard is active."""
    if command_succeeds("systemctl", "is-enabled", "--quiet", "usbguard"):
        status = PASS
        note = None
        rec = None
        if command_succeeds("systemctl", "is-failed", "--quiet", "usbguard"):
            status = status.downgrade_to(WARN)
            note = Note(_("USBGuard is enabled but has failed to run."), WARN)
    else:
        status = FAIL
        note = Note(_("USBGuard is not enabled."), FAIL)
        rec_lines = [
            note.text,
            _("To set up USBGuard, run:"),
            "$ ujust setup-usbguard",
            _(
                "Caution: if you have already set up USBGuard, this will overwrite the existing policy."
            ),
        ]
        rec = "\n".join(rec_lines)
    yield Report(_("Ensuring USBGuard is active"), status, notes=note, recs=rec)


@audit
def audit_chronyd():
    """Ensure chronyd is active."""
    if command_succeeds("systemctl", "is-enabled", "--quiet", "chronyd"):
        status = PASS
        note = None
        rec = None
        if command_succeeds("systemctl", "is-failed", "--quiet", "chronyd"):
            status = status.downgrade_to(WARN)
            note = Note(_("{0} is enabled but has failed to run.").format("chronyd"), WARN)
    else:
        status = FAIL
        note = Note(_("{0} is not enabled.").format("chronyd"), FAIL)
        rec_lines = [
            note.text,
            _("To start and enable it, run:"),
            "$ systemctl enable --now chronyd",
        ]
        rec = "\n".join(rec_lines)
    yield Report(_("Ensuring chronyd is active"), status, notes=note, recs=rec)


@audit
@depends_on("audit_signed_image")
def audit_dns(state):
    """Ensure system DNS resolution is active and secure."""

    # Parse `ujust dns-selector status` output.
    status_out = command_stdout(
        "/usr/bin/python3", "/usr/libexec/secureblue/dns_selector.py", "status"
    )
    flags = {}
    for line in status_out.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        flags[key.strip()] = value.strip()

    global_dns = flags.get("Global DNS") == "enabled"
    dnssec = flags.get("DNSSEC") == "enabled"
    trivalent_doh = flags.get("Trivalent DoH") == "enabled"
    unbound = flags.get("DNS Resolver") == "Unbound"

    recs = []
    notes = []
    status = PASS

    # INFO
    if not trivalent_doh and state["image"].is_desktop():
        status = INFO
        notes.append(Note(_("DNS over HTTPS in Trivalent is disabled."), INFO))
        recs.append(
            "\n".join(
                [
                    _("Consider using DNS over HTTPS in Trivalent to hide queries."),
                    _("However, if you use a VPN, this may cause DNS leaks."),
                    _("To enable it, run:"),
                    "$ ujust dns-selector",
                ]
            )
        )

    # WARN
    if unbound and not global_dns:
        status = WARN
        notes.append(Note(_("Secure global DNS is not configured."), WARN))
        recs.append(
            "\n".join(
                [
                    _("Consider using secure global DNS."),
                    _("However, if you use a VPN, this may cause DNS leaks."),
                    _("To enable it, run:"),
                    "$ ujust dns-selector",
                ]
            )
        )
    if not unbound:
        status = WARN
        notes.append(Note(_("The secure DNS resolver is not in use, possibly for a VPN."), WARN))
        recs.append(
            "\n".join(
                [
                    _("To view or reset your current DNS configuration, run:"),
                    "$ ujust dns-selector",
                ]
            )
        )

    # FAIL
    if unbound and not dnssec:
        status = FAIL
        notes.append(Note(_("Local DNSSEC validation is disabled."), FAIL))
        recs.append(
            "\n".join(
                [
                    _("You should enable local DNSSEC validation to prevent DNS hijacking."),
                    _("To enable it, run:"),
                    "$ ujust dns-selector dnssec on",
                ]
            )
        )
    if unbound and not global_dns and is_using_vpn():
        status = FAIL
        notes.append(
            Note(_("Using a VPN alongside Unbound without Global DNS may cause DNS leaks."), FAIL)
        )
        recs.append(
            "\n".join(
                [
                    _("If you use a VPN, switch your DNS resolver to systemd-resolved:"),
                    "$ ujust dns-selector resolver resolved",
                ]
            )
        )

    # Since we evaluate INFO -> WARN -> FAIL, put the most important ones first.
    notes.reverse()
    recs.reverse()

    yield Report(_("Ensuring system DNS resolution is secure"), status, notes=notes, recs=recs)


@audit
def audit_mac_randomization():
    """Ensure MAC randomization is enabled."""
    status = FAIL
    note = None
    conf_path = "/etc/NetworkManager/conf.d/rand_mac.conf"
    try:
        with open(conf_path, encoding="utf-8") as f:
            config = parse_config(f)
    except FileNotFoundError:
        pass
    except PermissionError:
        status = UNKNOWN
        note = Note(_("Unable to read file {0}.").format(conf_path), UNKNOWN)
    else:
        ethernet = config.get("ethernet.cloned-mac-address") in ("random", "stable")
        wifi = config.get("wifi.cloned-mac-address") in ("random", "stable")
        if ethernet and wifi:
            status = PASS
    if status == FAIL:
        rec_lines = [
            _("MAC randomization is not enabled."),
            _("To enable it, run:"),
            "$ ujust toggle-mac-randomization",
        ]
        rec = "\n".join(rec_lines)
    else:
        rec = None
    yield Report(_("Ensuring MAC randomization is enabled"), status, notes=note, recs=rec)


@audit
def audit_rpm_ostree_timer():
    """Ensure rpm-ostree automatic updates are enabled."""
    status = PASS
    notes = []
    recs = []

    if not command_succeeds("systemctl", "is-enabled", "--quiet", "rpm-ostreed-automatic.timer"):
        status = FAIL
        note_text = _("{0} is disabled.").format("rpm-ostreed-automatic.timer")
        notes.append(Note(note_text, FAIL))
        rec_lines = [
            note_text,
            _("To enable it, run:"),
            "$ systemctl enable --now rpm-ostreed-automatic.timer",
        ]
        recs.append("\n".join(rec_lines))
    elif command_succeeds("systemctl", "is-failed", "--quiet", "rpm-ostreed-automatic.service"):
        status = status.downgrade_to(WARN)
        notes.append(
            Note(_("{0} has failed to run.").format("rpm-ostreed-automatic.service"), WARN)
        )

    bad_rpm_ostreed_conf = False
    try:
        config = configparser.ConfigParser()
        config.read("/etc/rpm-ostreed.conf")
        if config["Daemon"].get("AutomaticUpdatePolicy") not in ("stage", "apply"):
            bad_rpm_ostreed_conf = True
    except (configparser.Error, KeyError):
        bad_rpm_ostreed_conf = True

    if bad_rpm_ostreed_conf:
        status = FAIL
        note_text = _("Automatic system updates are disabled in /etc/rpm-ostreed.conf")
        notes.append(Note(note_text, FAIL))
        rec_lines = [
            note_text,
            _("To fix this, run:"),
            "$ run0 -i cp /usr/etc/rpm-ostreed.conf /etc/rpm-ostreed.conf",
        ]
        recs.append("\n".join(rec_lines))

    yield Report(_("Ensuring automatic system updates are enabled"), status, notes=notes, recs=recs)


@audit
def audit_podman_auto_update():
    """Ensure podman automatic updates are enabled."""
    status = PASS
    note = None
    rec = None
    if not command_succeeds("systemctl", "is-enabled", "--quiet", "podman-auto-update.timer"):
        status = FAIL
        note = Note(_("{0} is disabled.").format("podman-auto-update.timer"), FAIL)
        rec_lines = [
            note.text,
            _("To enable it, run:"),
            "$ systemctl enable --now podman-auto-update.timer",
        ]
        rec = "\n".join(rec_lines)
    elif command_succeeds("systemctl", "is-failed", "--quiet", "podman-auto-update.service"):
        status = status.downgrade_to(WARN)
        note = Note(_("{0} has failed to run.").format("podman-auto-update.service"), WARN)

    yield Report(
        _("Ensuring {0} is enabled").format("podman-auto-update.timer"),
        status,
        notes=note,
        recs=rec,
    )


@audit
@depends_on("audit_container_userns")
def audit_podman_global_auto_update(state):
    """Ensure podman automatic updates are enabled globally."""
    status = PASS
    note = None
    rec = None
    if not command_succeeds(
        "systemctl", "--global", "is-enabled", "--quiet", "podman-auto-update.timer"
    ):
        status = FAIL
        note = Note(_("{0} is not enabled globally.").format("podman-auto-update.timer"), FAIL)
        rec_lines = [
            note.text,
            _("To enable it, run:"),
            "$ systemctl enable --global --now podman-auto-update.timer",
        ]
        rec = "\n".join(rec_lines)
    elif state["container_userns_enabled"] and command_succeeds(
        "systemctl", "--user", "is-failed", "--quiet", "podman-auto-update.service"
    ):
        status = status.downgrade_to(WARN)
        note = Note(_("{0} has failed to run.").format("podman-auto-update.service"), WARN)

    yield Report(
        _("Ensuring {0} is enabled globally").format("podman-auto-update.timer"),
        status,
        notes=note,
        recs=rec,
    )


@audit
def audit_flatpak_auto_update():
    """Ensure flatpak automatic updates are enabled."""
    if not command_succeeds("command", "-v", "flatpak"):
        return
    status = PASS
    note = None
    rec = None
    if not command_succeeds(
        "systemctl", "--global", "is-enabled", "--quiet", "flatpak-user-update.timer"
    ):
        status = FAIL
        note = Note(_("{0} is not enabled globally.").format("flatpak-user-update.timer"), FAIL)
        rec_lines = [
            note.text,
            _("To enable it, run:"),
            "$ systemctl enable --global --now flatpak-user-update.timer",
        ]
        rec = "\n".join(rec_lines)
    elif command_succeeds(
        "systemctl", "--user", "is-failed", "--quiet", "flatpak-user-update.service"
    ):
        status = status.downgrade_to(WARN)
        note = Note(_("{0} has failed to run.").format("flatpak-user-update.service"), WARN)

    yield Report(
        _("Ensuring {0} is enabled globally").format("flatpak-user-update.timer"),
        status,
        notes=note,
        recs=rec,
    )

    status = PASS
    note = None
    rec = None
    if not command_succeeds("systemctl", "is-enabled", "--quiet", "flatpak-system-update.timer"):
        status = FAIL
        note = Note(_("{0} is not enabled.").format("flatpak-system-update.timer"), FAIL)
        rec_lines = [
            note.text,
            _("To enable it, run:"),
            "$ systemctl enable --now flatpak-system-update.timer",
        ]
        rec = "\n".join(rec_lines)
    elif command_succeeds("systemctl", "is-failed", "--quiet", "flatpak-system-update.service"):
        status = status.downgrade_to(WARN)
        note = Note(_("{0} has failed to run.").format("flatpak-system-update.service"), WARN)

    yield Report(
        _("Ensuring {0} is enabled").format("flatpak-system-update.timer"),
        status,
        notes=note,
        recs=rec,
    )


@audit
def audit_brew_auto_update():
    """Ensure Homebrew automatic updates are enabled."""
    if not command_succeeds("command", "-v", "brew"):
        return
    status = PASS
    disabled_timers = []
    notes = []
    rec = None
    for unit in ("brew-update", "brew-upgrade"):
        timer = f"{unit}.timer"
        service = f"{unit}.service"
        if not command_succeeds("systemctl", "--global", "is-enabled", "--quiet", timer):
            status = FAIL
            disabled_timers.append(timer)
            notes.append(Note(_("{0} is not enabled.").format(timer), FAIL))
        elif command_succeeds("systemctl", "--user", "is-failed", "--quiet", service):
            status = status.downgrade_to(WARN)
            notes.append(Note(_("{0} has failed to run.").format(service), WARN))

    if disabled_timers:
        rec = "\n".join(
            (
                _("Automatic updates for Homebrew are not enabled."),
                _("To enable them, run:"),
                f"$ systemctl enable --global --now {' '.join(disabled_timers)}",
            )
        )

    yield Report(
        _("Ensuring automatic Homebrew updates are enabled"),
        status,
        notes=notes,
        recs=rec,
    )


@audit
def audit_groups():
    """Check whether user is in known groups with security implications."""
    user_groups = frozenset(command_stdout("groups").split())

    if "wheel" in user_groups:
        rec_lines = [
            _("The current user is in the wheel group."),
            _("To set up a separate wheel account, run:"),
            "$ ujust create-admin",
        ]
        rec = "\n".join(rec_lines)
        status = FAIL
    else:
        rec = None
        status = PASS
    yield Report(_("Ensuring user is not a member of the wheel group"), status, recs=rec)

    username = getpass.getuser()
    known_groups = (username, "usbguard", "wheel")
    dangerous_groups = ("docker", "libvirt")
    status = PASS
    notes = []
    recs = []
    for group in user_groups:
        remove_group_cmd = f"$ run0 -i usermod -rG {group} {username}"
        if group in known_groups:
            continue
        elif group in dangerous_groups:
            status = status.downgrade_to(FAIL)
            note = Note(_("The current user is in the group '{0}'.").format(group), FAIL)
            notes.append(note)
            rec_lines = [
                note.text,
                _("This allows privilege escalation to root."),
                _("To remove the user from this group, run:"),
                remove_group_cmd,
            ]
            recs.append("\n".join(rec_lines))
        elif group == "systemd-journal":
            status = status.downgrade_to(WARN)
            note = Note(_("The current user is in the group '{0}'.").format(group), WARN)
            notes.append(note)
            rec_lines = [
                note.text,
                _("This group allows the user to read system and kernel logs."),
                _("This might make it easier to exploit kernel vulnerabilities."),
                _("To remove the user from this group, run:"),
                remove_group_cmd,
            ]
            recs.append("\n".join(rec_lines))
        else:
            status = status.downgrade_to(WARN)
            note = Note(
                _("The current user is in the unrecognized group '{0}'.").format(group), WARN
            )
            notes.append(note)
            rec_lines = [
                note.text,
                _("Group memberships can grant additional privileges and may pose security risks."),
                _("You may want to consider removing the user from this group:"),
                remove_group_cmd,
            ]
            recs.append("\n".join(rec_lines))
    yield Report(
        _("Checking if user is in groups with security implications"),
        status,
        notes=notes,
        recs=recs,
    )


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
        rec_lines = [
            _("Xwayland is enabled for {0}.").format(de),
            _("To disable it, run:"),
            "$ ujust set-xwayland off",
        ]
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
        rec_lines = [
            _("GNOME user extensions are enabled."),
            _("To disable this, run:"),
            "$ ujust toggle-gnome-extensions",
        ]
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
        rec_lines = [
            _("SELinux is in Permissive mode."),
            _("To set it to Enforcing mode, run:"),
            "$ run0 -i setenforce 1",
        ]
        rec = "\n".join(rec_lines)
    yield Report(_("Ensuring SELinux is in Enforcing mode"), status, recs=rec)


@audit
def audit_environment_file():
    """Ensure /etc/environment has not been modified."""
    env_file = "/etc/environment"
    status = PASS
    note = None
    rec = None
    try:
        if not filecmp.cmp("/usr" + env_file, env_file):
            status = WARN
            note = Note(_("The file {0} has been modified.").format(env_file), WARN)
    except FileNotFoundError:
        status = WARN
        note = Note(_("The file {0} has been deleted.").format(env_file), WARN)
    except PermissionError:
        status = WARN
        note = Note(_("The file {0} cannot be read.").format(env_file), WARN)
    if status != PASS:
        rec_lines = [
            _("The file {0} has been modified.").format(env_file),
            _("To reset it, run:"),
            f"$ run0 -i cp -p /usr{env_file} {env_file}",
        ]
        rec = "\n".join(rec_lines)
    yield Report(_("Ensuring no environment file overrides"), status, notes=note, recs=rec)


@audit
@depends_on("audit_signed_image")
def audit_kde_ghns(state):
    """Ensure KDE GHNS is disabled."""
    if state["image"] != Image.KINOITE:
        return
    status = FAIL
    note = None
    try:
        with open("/etc/xdg/kdeglobals", encoding="utf-8") as f:
            config = parse_config(f)
    except (FileNotFoundError, PermissionError):
        status = WARN
        note = Note(
            _("The file {0} was not found or inaccessible.").format("/etc/xdg/kdeglobals"), WARN
        )
    else:
        if config.get("ghns") == "false":
            status = PASS
    if status == FAIL:
        rec_lines = [
            _("KDE GNHS is enabled."),
            _("To disable it, run:"),
            "$ ujust toggle-ghns",
        ]
        rec = "\n".join(rec_lines)
    else:
        rec = None
    yield Report(_("Ensuring KDE GHNS is disabled"), status, notes=note, recs=rec)


@audit
def audit_ld_preload():
    """Ensure ld.so.preload exists and is readable only by root."""
    status = PASS
    notes = []
    rec = None
    ld_so_preload = "/etc/ld.so.preload"
    try:
        stat_result = os.stat(ld_so_preload)
    except FileNotFoundError:
        status = FAIL
        notes.append(Note(_("The file {0} was not found.").format(ld_so_preload), FAIL))
    else:
        mode = stat.S_IMODE(stat_result.st_mode)
        expected_mode = 0o600
        if mode != expected_mode:
            status = WARN
            notes.append(
                Note(
                    _("{0} has mode {1:o} (expected {2:o})").format(
                        ld_so_preload, mode, expected_mode
                    ),
                    WARN,
                )
            )
        if stat_result.st_uid != 0:
            status = FAIL
            notes.append(Note(_("{0} is owned by a non-root user!").format(ld_so_preload), FAIL))
    if status != PASS:
        rec_lines = [
            _("The file {0} has been modified or deleted.").format(ld_so_preload),
            _("To reset it and enable hardened_malloc for system processes, run:"),
            f"$ run0 -i cp -p /usr{ld_so_preload} {ld_so_preload}",
        ]
        rec = "\n".join(rec_lines)
    yield Report(
        _("Ensuring {0} has expected permissions").format("ld.so.preload"),
        status,
        notes=notes,
        recs=rec,
    )


@audit
def audit_hardened_malloc():
    """Ensure hardened_malloc is set to be preloaded in place of the default system malloc."""
    rec = None
    ld_preload = os.environ.get("LD_PRELOAD")
    preloads = [] if ld_preload is None else ld_preload.split()
    expected_preloads = ["libhardened_malloc.so", "libno_rlimit_as.so"]
    if preloads == expected_preloads:
        status = PASS
        note = None
    elif "libhardened_malloc.so" in preloads:
        status = WARN
        note = Note(
            _("{0} is set, but {1} has been modified.").format("hardened_malloc", "LD_PRELOAD"),
            WARN,
        )
    elif "libhardened_malloc-light.so" in preloads:
        status = WARN
        note = Note(
            _("The '{0}' variant of {1} has been set.").format("light", "hardened_malloc"), WARN
        )
    elif "libhardened_malloc-pkey.so" in preloads:
        status = WARN
        note = Note(
            _("The '{0}' variant of {1} has been set.").format("pkey", "hardened_malloc"), WARN
        )
    else:
        status = FAIL
        note = Note(_("{0} has not been set.").format("LD_PRELOAD=libhardened_malloc.so"), FAIL)

    if status != PASS:
        rec = _("""The environment variable {0} has been modified or is unset.
                Check that {1} has not been overridden in
                {2} or related configuration files.""").format(
            "LD_PRELOAD", "LD_PRELOAD=libhardened_malloc.so", "/etc/profile.d"
        )
    yield Report(
        _("Ensuring hardened_malloc is set to be preloaded"),
        status,
        notes=note,
        recs=rec,
    )


@audit
def audit_secureboot():
    """Ensure secureboot is enabled."""
    note = None
    rec = None

    result = subprocess.run(
        ["/usr/bin/mokutil", "--sb-state"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0 and result.stdout.strip() == "SecureBoot enabled":
        status = PASS
    elif (
        "doesn't support Secure Boot" in result.stderr
        or "EFI variables are not supported" in result.stderr
    ):
        status = INFO
        note = Note(_("Your hardware does not support secure boot."), INFO)
        rec = (
            note.text
            + "\n"
            + _(
                "The system will be unable to verify that kernel modules are signed or the boot process."
            )
        )
    else:
        status = FAIL

    yield Report(_("Ensuring secure boot is enabled"), status, notes=note, recs=rec)


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
        rec_lines = [
            _("Bash environment is not locked down."),
            _("The following files do not appear to be immutable or do not exist:"),
            *unlocked_files,
            _("To fix this, run:"),
            "$ ujust toggle-bash-environment-lockdown",
        ]
        rec = "\n".join(rec_lines)
    else:
        status = PASS
        rec = None
    yield Report(_("Ensuring current user's bash environment is locked down"), status, recs=rec)


@audit
def audit_print_services():
    """Check whether printing services are disabled."""
    status = PASS
    notes = []
    recs = []
    cups = "cups.service"
    cups_browsed = "cups-browsed.service"
    cups_status, cups_browsed_status = command_stdout(
        "systemctl", "is-enabled", cups, cups_browsed, check=False
    ).splitlines()

    match cups_status:
        case "enabled":
            status = status.downgrade_to(WARN)
            note = _("CUPS (the printing service) is enabled.")
            notes.append(Note(note, WARN))
            recs.append("\n".join([note, _("To fix this, run:"), "$ ujust toggle-cups"]))
        case "disabled":
            status = status.downgrade_to(INFO)
            note = _("CUPS (the printing service) is disabled, but unmasked.")
            notes.append(Note(note, INFO))
            recs.append("\n".join([note, _("To fix this, run:"), "$ ujust toggle-cups"]))
        case "masked":
            pass
        case _:
            status = status.downgrade_to(WARN)
            note = _("CUPS (the printing service) has unexpected status '{0}'.").format(cups_status)
            notes.append(Note(note, WARN))

    match cups_browsed_status:
        case "enabled":
            status = status.downgrade_to(FAIL)
            note = _("{0} is enabled.").format(cups_browsed)
            notes.append(Note(note, FAIL))
            recs.append(
                "\n".join(
                    [
                        note,
                        _("To fix this, run:"),
                        f"$ systemctl disable --now {cups_browsed}",
                        f"$ systemctl mask {cups_browsed}",
                    ]
                )
            )
        case "disabled":
            status = status.downgrade_to(WARN)
            note = _("{0} is disabled, but unmasked.").format(cups_browsed)
            notes.append(Note(note, WARN))
            recs.append(
                "\n".join(
                    [
                        note,
                        _("To fix this, run:"),
                        f"$ systemctl mask {cups_browsed}",
                    ]
                )
            )
        case "masked":
            pass
        case _:
            status = status.downgrade_to(FAIL)
            note = _("{0} has unexpected status '{1}'.").format(cups_browsed, cups_status)
            notes.append(Note(note, FAIL))

    yield Report(_("Ensuring printing services are disabled"), status, notes=notes, recs=recs)


@audit
def audit_webcam_module():
    """Ensure Webcam module is disabled."""
    webcam_mod_file = "/etc/modprobe.d/99-disable-webcam.conf"
    status = UNKNOWN
    rec = None
    note = None
    try:
        with open(webcam_mod_file, encoding="utf-8") as f:
            if f.read().strip() == "install uvcvideo /bin/false":
                if is_module_loaded("uvcvideo"):
                    status = INFO
                    rec_lines = [
                        _("Webcam module is blacklisted in {0} but is still enabled.").format(
                            webcam_mod_file
                        ),
                        _("To disable it, you must reboot."),
                    ]
                else:
                    status = PASS
    except FileNotFoundError:
        status = INFO
        rec_lines = [
            _("Webcam module is enabled."),
            _("To disable it, run:"),
            "$ ujust set-webcam-modules off",
        ]
    except PermissionError:
        note = Note(_("Unable to read file {0}.").format(webcam_mod_file), UNKNOWN)

    if status == INFO:
        rec = "\n".join(rec_lines)
        note = Note(_("Webcam module is enabled."), INFO)

    yield Report(_("Checking whether webcam module is disabled"), status, notes=note, recs=rec)


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
        note = None
        if url not in [
            "https://dl.flathub.org/repo/",
            "https://dl.flathub.org/beta-repo/",
        ]:
            status = FAIL
            note = Note(_("{0} is configured with an unknown URL.").format(name), FAIL)
        elif subset != "verified":
            status = FAIL
            note = Note(_("{0} is not a verified flatpak repository.").format(name), FAIL)
        else:
            status = PASS
        yield Report(_("Auditing flatpak remote {0}").format(name), status, notes=note)


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
            notes=flatpak_permissions_state.notes,
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
    # Translatable strings printed by argparse that we want to ensure are included in the PO files.
    _argparse_translatable_strings = (  # noqa: RUF100, F841
        _("usage: "),
        _("options"),
        _("show this help message and exit"),
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
