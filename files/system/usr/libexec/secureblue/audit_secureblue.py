#!/usr/bin/env python3

import argparse, asyncio, enum, filecmp, inspect, os.path, re, subprocess
from collections.abc import Callable
from subprocess import CalledProcessError
from typing import Any, AsyncGenerator, Generator, NewType, Self

class AuditError(Exception):
    """Base class for audit errors."""

class DependencyError(AuditError):
    """A check's dependency requirements were not satisfied."""

class Status(enum.Enum):
    """Status of a system check."""
    SUCCESS = enum.auto()
    WARNING = enum.auto()
    FAILURE = enum.auto()

    def in_color(self) -> str:
        """Colored text representation of the status."""
        match self:
            case Status.SUCCESS:
                color_code = 32 # green
            case Status.WARNING:
                color_code = 33 # yellow
            case Status.FAILURE:
                color_code = 31 # red
        return f"\x1b\x5b{color_code}m{self.name}\x1b\x5b39m"

SUCCESS = Status.SUCCESS
WARNING = Status.WARNING
FAILURE = Status.FAILURE

class Report:
    """A result of a check to be reported."""
    def __init__(self, desc: str, status: Status, warnings: str | list[str] = []):
        self.description = desc
        self.status = status
        if isinstance(warnings, str):
            self.warnings = [warnings]
        else:
            self.warnings = warnings

    def __str__(self) -> str:
        s = f"{self.description + "...":<68} [ {self.status.in_color()} ]"
        for warning in self.warnings:
            s += f"\n> {warning}"
        return s

class Check:
    """A single check done as part of an audit."""
    def __init__(
        self,
        name: str,
        call: AsyncGenerator[Any, [dict[str, Any]]],
        category: str | None = None,
        depends: list[str] = []
    ):
        self.name = name
        self.call = call
        self.category = category
        self.depends = depends
        self.done = False
        self.reports: list[Report] = []
        self.recs: list[str] = []

    async def run(self, state: dict[str, Any], rerun: bool = False) -> AsyncGenerator[Report, ...]:
        """Run the check and store the results."""
        if self.done and not rerun:
            return
        async for result in (self.call)(state):
            if isinstance(result, tuple):
                report, recs = result
                if not isinstance(recs, list):
                    if recs is None:
                        recs = []
                    else:
                        recs = [recs]
                self.reports.append(report)
                self.recs += recs
                yield report
            else:
                yield result
        self.done = True

def bold(text: str) -> str:
    return f"\x1b\x5b1m{text}\x1b\x5b22m"

def print_heading(text: str, width: int = 80):
    print(f"\n\x1b\x5b1;38;5;228m\x1b\x5b48;5;63m{text}\x1b\x5b0m")
    print("=" * width)

class Audit:
    """A system audit."""
    def __init__(self):
        self.checks: list[Check] = []
        self.state: dict[str, Any] = {}
        self.recs: list[str] = []
        self.categories: list[str] = []

    def names(self) -> list[str]:
        """Get a list of the names of all checks."""
        return [check.name for check in self.checks]

    def add_check(self, check: Check):
        names = self.names()
        for dep in check.depends:
            if dep not in names:
                raise DependencyError(f"'{check.name}' requires '{dep}' to be run first.")
        if check.category is not None:
            self.categories.append(check.category)
        self.checks.append(check)

    async def run(self, exclude: list[str] = []):
        print_heading("Audit")
        for check in self.checks:
            if check.category in exclude:
                continue
            async for report in check.run(self.state):
                print(report)
            self.recs += check.recs
        print_heading("Recommendations")
        for rec in self.recs:
            rec_lines = [line.strip() for line in rec.split("\n")]
            for i in range(len(rec_lines)):
                if not rec_lines[i]:
                    continue
                if rec_lines[i][0] in ["$", "#"]:
                    rec_lines[i] = bold(rec_lines[i])
            print("\n  ".join(rec_lines) + "\n")

global_audit = Audit()

def make_check(
    f: Check | AsyncGenerator[Any, [dict[str, Any]]] | Generator[Any, [dict[str, Any]]]
) -> Check:
    """Make a Check object from a generator."""
    if isinstance(f, Check):
        return f
    elif inspect.isasyncgenfunction(f):
        return Check(name=f.__name__, call=f)
    else:
        async def f_async(*args, **kwargs):
            for item in f(*args, **kwargs):
                yield item
        return Check(name=f.__name__, call=f_async)

def audit(
    f: Check | AsyncGenerator[Any, [dict[str, Any]]]
) -> Check:
    """Add a check to the global audit system."""
    check = make_check(f)
    global_audit.add_check(check)
    return check

def depends(deps: str | list[str]) -> Callable[..., Check]:
    """Add a dependency to a check."""
    if isinstance(deps, str):
        deps = [deps]
    def add_dependencies(f) -> Check:
        check = make_check(f)
        check.depends = deps
        return check
    return add_dependencies

def category(cat: str) -> Callable[..., Check]:
    """Add a dependency to a check."""
    def add_category(f) -> Check:
        check = make_check(f)
        check.category = cat
        return check
    return add_category

def command_stdout(args: str | list[str], check: bool = True) -> str:
    """Run a command in the shell and return the contents of stdout."""
    return subprocess.run(args, capture_output=True, check=check, text=True).stdout.strip()

async def async_command_stdout(args: list[str]) -> str:
    """Asynchronously run a command in the shell and return the contents of stdout."""
    sub = await asyncio.create_subprocess_exec(*args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    await sub.wait()
    if sub.returncode != 0:
        err = f"async command `{" ".join(args)}` returned nonzero exit code {sub.returncode}"
        raise CalledProcessError(err)
    output = await sub.stdout.read()
    return output.decode("utf-8", errors="replace").strip()

def command_succeeds(args: str | list[str]) -> bool:
    """Run a command in the shell and return the contents of stdout."""
    return subprocess.run(args, capture_output=True).returncode == 0

###############################################################################
# Checks to be run go below this line.
###############################################################################

@audit
def audit_kargs(_state):
    """Check for hardened kernel arguments."""
    kargs_current = command_stdout(["rpm-ostree", "kargs"]).split()
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
        "kvm-intel.vmentry_l1d_flush=always"
    ]
    reports = []
    for karg in kargs_expected:
        status = SUCCESS if karg in kargs_current else FAILURE
        yield Report(f"Checking for {karg} karg", status)

@audit
def audit_sysctl(_state):
    """Check for sysctl overrides."""
    with open("/usr/etc/sysctl.d/60-hardening.conf", "r") as f:
        conf = f.readlines()
    sysctl_expected = {}
    for line in conf:
        line = line.strip()
        if not line or line[0] == "#":
            continue
        key, value = line.split("=", maxsplit=1)
        sysctl_expected[key.strip()] = value.strip()
    status = SUCCESS
    sysctl_errors = []
    with open("/etc/sysctl.d/60-hardening.conf", "r") as f:
        etc_conf = f.readlines()
    if conf != etc_conf:
        status = WARNING
        sysctl_errors.append("/etc/sysctl.d/60-hardening.conf has been modified")
    for sysctl, expected in sysctl_expected.items():
        try:
            actual = command_stdout(["sysctl", "-bn", sysctl])
        except CalledProcessError:
            continue
        actual = re.sub(r"\s+", " ", actual)
        if actual != expected and expected != "0" and actual != "disabled":
            status = FAILURE
            sysctl_errors.append(f"{sysctl} should be {expected}, found {actual}")
    yield Report("Ensuring no sysctl overrides", status, warnings=sysctl_errors)

@audit
def audit_signed_image(_state):
    """Check that the secureblue image is signed."""
    ostree_status = command_stdout(["rpm-ostree", "status"])
    if "● ostree-image-signed" in ostree_status:
        status = SUCCESS
        recs = None
    else:
        status = FAILURE
        recs = """The current image is not signed.
            To rebase to a signed image download and run or re-run install_secureblue.sh from the secureblue github"""
    yield Report("Ensuring a signed image is in use", status), recs

@audit
def audit_modprobe(state):
    """Check that the kernel module blacklist has not been overridden."""
    with open("/usr/etc/modprobe.d/blacklist.conf", "r") as f:
        conf = f.readlines()
    blacklisted_modules = []
    for line in conf:
        words = line.strip().split()
        if words and words[0] in ["blacklist", "install"]:
            blacklisted_modules.append(words[1])
    unwanted_modules = []
    with open("/proc/modules", "r") as f:
        for line in f.readlines():
            mod = line.split()[0]
            if mod in blacklisted_modules:
                unwanted_modules.append(mod)
    unwanted_modules.sort()
    status = SUCCESS
    warnings = []
    with open("/etc/modprobe.d/blacklist.conf", "r") as f:
        if f.readlines() != conf:
            status = WARNING
            warnings.append("/etc/modprobe.d/blacklist.conf has been modified")
    for mod in unwanted_modules:
        status = FAILURE
        warnings.append(f"{mod} is in blacklist.conf but it is loaded")
    state["bluetooth_loaded"] = "bluetooth" in unwanted_modules
    yield Report("Ensuring no modprobe overrides", status, warnings)

@audit
def audit_ptrace(state):
    with open("/proc/sys/kernel/yama/ptrace_scope", "r") as f:
        if f.read().strip() == "3":
            status = SUCCESS
            state["ptrace_allowed"] = False
        else:
            status = FAILURE
            state["ptrace_allowed"] = True
    yield Report("Ensuring ptrace is forbidden", status)

@audit
def audit_authselect(_state):
    AUTHSELECT_TEST_STRING="Ensuring no authselect overrides"
    cmp = filecmp.dircmp("/usr/etc/authselect", "/etc/authselect", shallow=False, ignore=[])
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        status = FAILURE
    else:
        status = SUCCESS
    yield Report("Ensuring no authselect overrides", status)

@audit
def audit_container_policy(_state):
    unmodified = filecmp.cmp("/usr/etc/containers/policy.json", "/etc/containers/policy.json")
    local_override = os.path.isfile(os.path.expanduser("~/.config/containers/policy.json"))
    if unmodified and not local_override:
        status = SUCCESS
    else:
        status = FAILURE
    yield Report("Ensuring no container policy overrides", status)

@audit
def audit_unconfined_userns(_state):
    if command_stdout(["ujust", "check-unconfined-userns-state"]) == "disabled":
        status = SUCCESS
        recs = None
    else:
        status = FAILURE
        recs = """Unconfined domain user namespace creation is permitted
                To disallow it, run:
                $ ujust toggle-unconfined-domain-userns-creation"""
    yield Report("Ensuring unconfined user namespace creation disallowed", status), recs

@audit
def audit_container_userns(_state):
    if command_stdout(["ujust", "check-container-userns-state"]) == "disabled":
        status = SUCCESS
        recs = []
    else:
        status = WARNING
        recs = """Container domain user namespace creation is permitted
                To disallow it, run:
                $ ujust toggle-container-domain-userns-creation"""
    yield Report("Ensuring container user namespace creation disallowed", status), recs

@audit
def audit_usbguard(_state):
    if command_succeeds("systemctl is-active --quiet usbguard".split()):
        status = SUCCESS
    else:
        status = FAILURE
    yield Report("Ensuring usbguard is active", status)

@audit
def audit_chronyd(_state):
    if command_succeeds("systemctl is-active --quiet chronyd".split()):
        status = SUCCESS
    else:
        status = FAILURE
    yield Report("Ensuring chronyd is active", status)

@audit
def audit_dns(_state):
    rec = None
    if command_succeeds("systemctl is-active --quiet systemd-resolved".split()):
        dnssec = False
        dot = False
        try:
            with open("/etc/systemd/resolved.conf.d/10-securedns.conf", "r") as f:
                for line in f.readlines():
                    if line.strip() == "DNSSEC=true":
                        dnssec = True
                    if line.strip() == "DNSOverTLS=true":
                        dot = True
                    if dnssec and dot:
                        break
        except FileNotFoundError:
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
    yield Report("Ensuring system DNS resolution is secure", status), rec

@audit
def audit_rpm_ostree_timer(_state):
    if command_succeeds("systemctl is-enabled --quiet rpm-ostreed-automatic.timer".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """rpm-ostreed-automatic.timer is disabled
                To enable, run:
                $ systemctl enable --now rpm-ostreed-automatic.timer"""
    yield Report("Ensuring rpm-ostreed-automatic.timer is enabled", status), rec

@audit
def audit_podman_auto_update(_state):
    if command_succeeds("systemctl is-enabled --quiet podman-auto-update.timer".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """podman-auto-update.timer is disabled
                To enable, run:
                $ systemctl enable --now podman-auto-update.timer"""
    yield Report("Ensuring podman-auto-update.timer is enabled", status), rec

@audit
def audit_podman_global_auto_update(_state):
    if command_succeeds("systemctl --global is-enabled --quiet podman-auto-update.timer".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """podman-auto-update.timer is not enabled globally
                To enable, run:
                $ systemctl enable --global podman-auto-update.timer"""
    yield Report("Ensuring podman-auto-update.timer is enabled globally", status), rec

@audit
def audit_flatpak_auto_update(_state):
    if not command_succeeds("command -v flatpak".split()):
        return
    if command_succeeds("systemctl --global is-enabled --quiet flatpak-user-update.timer".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """flatpak-user-update.timer is not enabled globally
                To enable, run:
                $ systemctl enable --global flatpak-user-update.timer"""
    yield Report("Ensuring flatpak-user-update.timer is enabled globally", status), rec

    if command_succeeds("systemctl is-enabled --quiet flatpak-system-update.timer".split()):
        status = SUCCESS
        rec = None
    else:
        status = FAILURE
        rec = """flatpak-system-update.timer is not enabled globally
                To enable, run:
                $ systemctl enable --now flatpak-system-update.timer"""
    yield Report("Ensuring flatpak-system-update.timer is enabled", status), rec

@audit
def audit_wheel(_state):
    if "wheel" in command_stdout("groups").split():
        status = FAILURE
    else:
        status = SUCCESS
    yield Report("Ensuring user is not a member of wheel", status)

@audit
def audit_xwayland(_state):
    if os.path.isfile("/etc/systemd/user/org.gnome.Shell@wayland.service.d/override.conf"):
        status = SUCCESS
    else:
        status = FAILURE
    yield Report("Ensuring xwayland is disabled for GNOME", status)

    if os.path.isfile("/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf"):
        status = SUCCESS
    else:
        status = FAILURE
    yield Report("Ensuring xwayland is disabled for KDE Plasma", status)

    if os.path.isfile("/etc/sway/config.d/99-noxwayland.conf"):
        status = SUCCESS
    else:
        status = FAILURE
    yield Report("Ensuring xwayland is disabled for Sway", status)

@audit
def audit_gnome_extensions(_state):
    if not command_succeeds("command -v gnome-shell".split()):
        return
    allowed = command_stdout("gsettings get org.gnome.shell allow-extension-installation".split())
    if allowed == "false":
        status = SUCCESS
    else:
        status = FAILURE
    yield Report("Ensuring GNOME user extensions are disabled", status)

@audit
def audit_selinux(_state):
    if command_stdout("getenforce") == "Enforcing":
        status = SUCCESS
    else:
        status = FAILURE
    yield Report("Ensuring SELinux is in Enforcing mode", status)

@audit
def audit_environment_file(_state):
    if filecmp.cmp("/usr/etc/environment", "/etc/environment"):
        status = SUCCESS
    else:
        status = WARNING
    yield Report("Ensuring no environment file overrides", status)

@audit
def audit_kde_ghns(_state):
    try:
        with open("/etc/xdg/kdeglobals", "r") as f:
            status = FAILURE
            for line in f.readlines():
                if line.strip() == "ghns=false":
                    status = SUCCESS
    except FileNotFoundError:
        return
    else:
        yield Report("Ensuring KDE GHNS is disabled", status)

@audit
def audit_hardened_malloc(_state):
    warnings = []
    try:
        with open("/etc/ld.so.preload", "r") as f:
            preloaded = f.read().split()
    except FileNotFoundError:
        status = FAILURE
        warnings.append("ld.so.preload not found")
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
    yield Report("Ensuring hardened_malloc is set in ld.so.preload", status, warnings)

@audit
def audit_secureboot(_state):
    if command_stdout(["mokutil", "--sb-state"], check=False) == "SecureBoot enabled":
        status = SUCCESS
    else:
        status = FAILURE
    yield Report("Ensuring secure boot is enabled", status)

@audit
def audit_bash_env_lockdown(_state):
    bash_env_paths = map(os.path.expanduser, [
        "~/.bashrc", "~/.bash_profile", "~/.config/bash-completion", "~/.profile",
        "~/.bash_logout", "~/.bash_login", "~/.bashrc.d/", "~/.config/environment.d/"
    ])
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
                immutable = "i" in command_stdout(cmd).split()[0]
            except CalledProcessError:
                immutable = False
            if not immutable:
                unlocked_files.append(path)
    if unlocked_files:
        status = FAILURE
        rec = f"""Bash environment is not locked down
                The following files do not appear to be immutable or do not exist:
                {"\n".join(unlocked_files)}
                To fix run:
                $ ujust toggle-bash-environment-lockdown"""
    else:
        status = SUCCESS
        rec = None
    yield Report("Ensuring current user's bash environment is locked down", status), rec

async def check_flatpak_permissions(name, version, state):
    """Check permissions for a single flatpak."""
    warnings = []
    recs = []
    status = SUCCESS
    perms_text = await async_command_stdout(["flatpak", "info", "--show-permissions", name, version])
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
            recs.append(f"""{name} has network access
                        To remove it use Flatseal or run:
                        $ flatpak override -u --unshare=network {name}""")
        if "ipc" in shared:
            status = FAILURE
            warnings.append(f"{name} has inter-process communications access")
            recs.append(f"""{name} has inter-process communications access
                        To remove it use Flatseal or run:
                        $ flatpak override -u --unshare=ipc {name}""")

    if "sockets" in perms:
        sockets = perms["sockets"]
        if "x11" in sockets and "fallback-x11" not in sockets:
            status = FAILURE
            warnings.append(f"{name} has x11 access")
            recs.append(f"""{name} has x11 access
                        To remove it use Flatseal or run:
                        $ flatpak override -u --nosocket=x11 {name}""")
        if "session-bus" in sockets:
            if status != FAILURE:
                status = WARNING
            warnings.append(f"{name} has access to the D-Bus session bus")
            recs.append(f"""{name} has access to the D-Bus session bus
                        To remove it use Flatseal or run:
                        $ flatpak override -u --nosocket=session-bus {name}""")
        if "system-bus" in sockets:
            if status != FAILURE:
                status = WARNING
            warnings.append(f"{name} has access to the D-Bus system bus")
            recs.append(f"""{name} has access to the D-Bus system bus
                        To remove it use Flatseal or run:
                        $ flatpak override -u --nosocket=system-bus {name}""")

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
        recs.append(f"""{name} is not requesting hardened_malloc
                    To enable it run:
                    $ ujust harden-flatpak {name}""")

    if not ("filesystems" in perms and "host-os:ro" in perms["filesystems"]):
        status = FAILURE
        warnings.append(f"{name} is missing host-os:ro permission")
        recs.append(f"""{name} is missing host-os:ro permission
                    This is required to load hardened_malloc.
                    To add it use Flatseal or run:
                    $ flatpak override -u --filesystem=host-os:ro {name}""")

    if "features" in perms:
        features = perms["features"]
        if state["bluetooth_loaded"] and "bluetooth" in features:
            status = FAILURE
            warnings.append(f"{name} has bluetooth access")
            recs.append(f"""{name} has bluetooth access
                        To remove it use Flatseal or run:
                        $ flatpak override -u --disallow=bluetooth {name}""")
        if state["ptrace_allowed"] and "devel" in features:
            status = FAILURE
            warnings.append(f"{name} has ptrace access")
            recs.append(f"""{name} has ptrace access
                        To remove it use Flatseal or run:
                        $ flatpak override -u --disallow=devel {name}""")

    if "devices" in perms and "all" in perms["devices"]:
        if status != FAILURE:
            status = WARNING
        warnings.append(f"""{name} has device=all permission""")
        recs.append(f"""{name} has device=all permission
                    This grants access to input devices, GPUs, raw USB, and virtualization
                    This may also be used as a sandbox escape vector
                    To remove it use Flatseal or run:
                    $ flatpak override -u --nodevice=all {name}
                    If GPU access is required, use device=dri instead:
                    $ flatpak override -u --device=dri {name}""")

    return name, version, status, warnings, recs

@audit
@category("flatpak")
@depends(["audit_modprobe", "audit_ptrace"])
async def audit_flatpaks(state):
    if not command_succeeds("command -v flatpak".split()):
        return

    remotes = command_stdout("flatpak remotes --columns=name,url,subset".split()).split("\n")
    for remote in remotes:
        name, url, subset = remote.split("\t")
        warnings = []
        if url not in ["https://dl.flathub.org/repo/", "https://dl.flathub.org/beta-repo/"]:
            status = FAILURE
            warnings.append(f"{name} is configured with an unknown url")
        elif subset != "verified":
            status = FAILURE
            warnings.append(f"{name} is not a verified repo")
        else:
            status = SUCCESS
        yield Report(f"Auditing flatpak remote {name}", status, warnings)

    flatpaks = []
    for line in command_stdout("flatpak list --columns=application,branch".split()).split("\n"):
        name, version = line.split("\t")
        flatpaks.append((name, version))
    flatpaks.sort()

    # dict to store results so they can be yielded in sorted order.
    # The boolean part of the value is whether the data has been sent yet.
    results = {key: (False, None) for key in flatpaks}
    checks = [check_flatpak_permissions(name, version, state) for name, version in flatpaks]
    async for result in asyncio.as_completed(checks):
        name, version, status, warnings, recs = await result
        results[(name, version)] = (False, (status, warnings, recs))
        # yield all lexicographically first results that are ready
        for (name, version), (sent, data) in results.items():
            if sent is True:
                continue
            if data is None:
                break
            (status, warnings, recs) = data
            yield Report(f"Auditing {name} ({version})", status, warnings), recs
            results[(name, version)] = (True, None)

async def main():
    parser = argparse.ArgumentParser()
    categories = ",".join(global_audit.categories)
    parser.add_argument("-s", "--skip", default="", help=f"skip categories ({categories})")
    args = parser.parse_args()
    skip = args.skip.split(",")
    await global_audit.run(exclude=skip)
    if "flatpak" in skip:
        print("flatpak settings not audited per user request.")
    else:
        print(f"Use option '{bold("--skip flatpak")}' to skip flatpak recommendations.")

if __name__ == "__main__":
    asyncio.run(main())

