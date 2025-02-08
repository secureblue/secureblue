# Audit secureblue
audit-secureblue:
    #!/bin/bash

    STATUS_SUCCESS="SUCCESS"
    STATUS_WARNING="WARNING"
    STATUS_FAILURE="FAILURE"
    print_status() {
        local check_name="$1"
        local status="$2"

        local color_code
        case "$status" in
            $STATUS_SUCCESS) color_code=32 ;; # Green
            $STATUS_WARNING) color_code=33 ;; # Yellow
            $STATUS_FAILURE) color_code=31 ;;    # Red
            *) color_code=0 ;;
        esac

        local formatted_status
        formatted_status=$(printf "%*s" $(( (7 + ${#status}) / 2 )) "$status")
        formatted_status=$(printf "%-7s" "$formatted_status")

        printf "%-64s [ \033[%dm%s\033[0m ]\n" "$check_name"... "$color_code" "$formatted_status"
    }

    if command -v gum >/dev/null 2>&1; then
        HAS_GUM=true
    else
        HAS_GUM=false
    fi
    print_heading() {
        echo
        if [[ $HAS_GUM == true ]]; then 
            gum style --bold --background=63 --foreground=228 "$1"
        else
            echo "$1"
        fi
        printf '=%.0s' {1..76}
        echo
    }
    hasPermission() {
        local permissions=$1
        local prefix=$2
        local query=$3
        local line=$(grep "^${prefix}=" <<< "$permissions" | sed -e "s/^${prefix}=//" -e "s/#.*//")
        IFS=';' read -r -a list <<< "$line"
        for p in ${list[@]}; do
            if [[ "$p" =~ ^$query$ ]]; then
                return
            fi
        done
        return 1
    }
    suggestions=()

    print_heading Audit

    KARGS=$(rpm-ostree kargs)
    KARGS_LIST=(
        "init_on_alloc=1"
        "init_on_free=1"
        "slab_nomerge"
        "page_alloc.shuffle=1"
        "randomize_kstack_offset=on"
        "vsyscall=none"
        "lockdown=confidentiality"
        "random.trust_cpu=off"
        "random.trust_bootloader=off"
        "iommu=force"
        "intel_iommu=on"
        "amd_iommu=force_isolation"
        "iommu.passthrough=0"
        "iommu.strict=1"
        "pti=on"
        "module.sig_enforce=1"
        "mitigations=auto,nosmt"
        "spectre_v2=on"
        "spec_store_bypass_disable=on"
        "l1d_flush=on"
        "gather_data_sampling=force"
        "efi=disable_early_pci_dma"
        "debugfs=off"
        "ia32_emulation=0"
        "l1tf=full,force"
        "kvm-intel.vmentry_l1d_flush=always"
    )

    for karg in "${KARGS_LIST[@]}"; do
        KARG_TEST_STRING="Checking for $karg karg"
        if echo "$KARGS" | grep -q "$karg"; then
            print_status "$KARG_TEST_STRING" "$STATUS_SUCCESS"
        else
            print_status "$KARG_TEST_STRING" "$STATUS_FAILURE"
        fi
    done

    SYSCTL_TEST_STRING="Ensuring no sysctl overrides"
    readarray -t sysctl_hardening_conf < <(grep -v -E -e "^#" -e "^$" </usr/etc/sysctl.d/60-hardening.conf)
    declare -A sysctl_hardening
    for line in "${sysctl_hardening_conf[@]}"; do
        parameter="$(sed -E -e "s/(.*) = .*/\1/"  <<<"$line")"
        value="$(sed -E "s/.* = (.*)/\1/" <<<"$line")"
        sysctl_hardening["$parameter"]+="$value"
    done
    sysctl_results="$(sysctl -a 2> >(grep -v "sysctl: permission denied on key "))"
    sysctl_errors=()
    for sysctl_parameter in "${!hardening[@]}"; do
        hardened_parameter_value="${hardening["$sysctl_parameter"]}"
        parameter_name="$(sed -E -e "s/\./\\\./g" -e "s/\*/\.\*/" <<<"$sysctl_parameter")"
        readarray -t sysctl_parameter_values < <(grep -E "^$key = " <<<"$sysctl_results")
        for parameter_value in "${sysctl_parameter_values[@]}"; do
            parameter_value="$(sed -E  -e "s/.* = (.*)/\1/" -e "s/\/ /g" <<<"$result" | tr -s " " )"
            if [[ "$parameter_value" != "$hardened_parameter_value" && ("$hardened_parameter_value" != 0 && "$parameter_value" != disabled) ]]; then
                sysctl_errors+=("$sysctl_parameter should be $hardened_parameter_value, found $parameter_value")
            fi
        done
    done
    if [[ "${#sysctl_errors}" == 0 ]] && diff /usr/etc/sysctl.d/60-hardening.conf /etc/sysctl.d/60-hardening.conf > /dev/null; then
        print_status "$SYSCTL_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$SYSCTL_TEST_STRING" "$STATUS_FAILURE"
        for error in "${sysctl_errors[@]}"; do
            echo "> $error"
        done
    fi

    SIGNED_IMAGE_TEST_STRING="Ensuring a signed image is in use"
    if rpm-ostree status | grep -q "● ostree-image-signed"; then
        print_status "$SIGNED_IMAGE_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$SIGNED_IMAGE_TEST_STRING" "$STATUS_FAILURE"
        suggestions+="The current image is not signed.	To rebase to a signed image download and run or re-run install_secureblue.sh from the secureblue github"
    fi

    MODPROBE_TEST_STRING="Ensuring no modprobe overrides"
    readarray -t unwanted_modules < <(comm -12 <(lsmod | cut -f 1 -d " " | sort) <(cat /usr/etc/modprobe.d/blacklist.conf | grep -E '^(blacklist)|(install)' | cut -f 2 -d " " | sort))
    if [[ "${#unwanted_modules[@]}" == 0 ]] && diff /usr/etc/modprobe.d/blacklist.conf /etc/modprobe.d/blacklist.conf > /dev/null; then
        print_status "$MODPROBE_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$MODPROBE_TEST_STRING" "$STATUS_FAILURE"
        for module in "${unwanted_modules[@]}"; do
            echo "> $module is in blacklist.conf but it is loaded"
            if [[ "$module" == "bluetooth" ]]; then
                bluetooth_loaded=true
            fi
        done
    fi

    PTRACE_TEST_STRING="Ensuring ptrace is forbidden"
    if [[ "$(cat /proc/sys/kernel/yama/ptrace_scope)" == 3 ]]; then
        print_status "$PTRACE_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$PTRACE_TEST_STRING" "$STATUS_FAILURE"
        ptrace_allowed=true
    fi

    AUTHSELECT_TEST_STRING="Ensuring no authselect overrides"
    if diff /usr/etc/authselect /etc/authselect --suppress-common-lines -r > /dev/null; then
        print_status "$AUTHSELECT_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$AUTHSELECT_TEST_STRING" "$STATUS_FAILURE"
    fi

    CONTAINER_POLICY_TEST_STRING="Ensuring no container policy overrides"
    if diff /usr/etc/containers/policy.json /etc/containers/policy.json > /dev/null && [ ! -f $HOME/.config/containers/policy.json ]; then
        print_status "$CONTAINER_POLICY_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$CONTAINER_POLICY_TEST_STRING" "$STATUS_FAILURE"
    fi

    USBGUARD_TEST_STRING="Ensuring usbguard is active"
    if systemctl is-active --quiet usbguard; then
        print_status "$USBGUARD_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$USBGUARD_TEST_STRING" "$STATUS_FAILURE"
    fi

    CHRONYD_TEST_STRING="Ensuring chronyd is active"
    if systemctl is-active --quiet chronyd; then
        print_status "$CHRONYD_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$CHRONYD_TEST_STRING" "$STATUS_FAILURE"
    fi

    SECUREDNS_TEST_STRING="Ensuring system DNS resolution is secure"
    if systemctl is-active --quiet systemd-resolved; then
        DNSSEC_STATUS="$(cat /etc/systemd/resolved.conf.d/10-securedns.conf | grep "DNSSEC")"
        DOT_STATUS="$(cat /etc/systemd/resolved.conf.d/10-securedns.conf | grep "DNSOverTLS")"
        if [[ "$DNSSEC_STATUS" == "DNSSEC=true" && "$DOT_STATUS" == "DNSOverTLS=true" ]]; then
            print_status "$SECUREDNS_TEST_STRING" "$STATUS_SUCCESS"
        else
            print_status "$SECUREDNS_TEST_STRING" "$STATUS_FAILURE"
            suggestions+="System DNS resolution is not secure	To select a secure resolver, run:	$ ujust dns-selector"
        fi
    else
        print_status "$SECUREDNS_TEST_STRING" "$STATUS_FAILURE"
        suggestions+="systemd-resolved is inactive	To start and enable it, run:	$ systemctl enable --now systemd-resolved"
    fi

    RPM_OSTREED_AUTOMATIC_TIMER_TEST_STRING="Ensuring rpm-ostreed-automatic.timer is enabled"
    if systemctl is-enabled --quiet rpm-ostreed-automatic.timer; then
        print_status "$RPM_OSTREED_AUTOMATIC_TIMER_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$RPM_OSTREED_AUTOMATIC_TIMER_TEST_STRING" "$STATUS_FAILURE"
        suggestions+="rpm-ostreed-automatic.timer is disabled	To enable, run:	$ systemctl enable --now rpm-ostreed-automatic.timer"
    fi

    PODMAN_AUTO_UPDATE_TIMER_TEST_STRING="Ensuring podman-auto-update.timer is enabled"
    if systemctl is-enabled --quiet podman-auto-update.timer; then
        print_status "$PODMAN_AUTO_UPDATE_TIMER_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$PODMAN_AUTO_UPDATE_TIMER_TEST_STRING" "$STATUS_FAILURE"
        suggestions+="podman-auto-update.timer is disabled	To enable, run:	$ systemctl enable --now podman-auto-update.timer"
    fi

    GLOBAL_PODMAN_AUTO_UPDATE_TIMER_TEST_STRING="Ensuring podman-auto-update.timer is enabled globally"
    if systemctl --global is-enabled --quiet podman-auto-update.timer; then
        print_status "$GLOBAL_PODMAN_AUTO_UPDATE_TIMER_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$GLOBAL_PODMAN_AUTO_UPDATE_TIMER_TEST_STRING" "$STATUS_FAILURE"
        suggestions+="podman-auto-update.timer is not enabled globally	To enable, run:	$ run0 systemctl enable --global podman-auto-update.timer"
    fi

    if command -v flatpak >/dev/null 2>&1; then
        FLATPAK_USER_UPDATE_TIMER_TEST_STRING="Ensuring flatpak-user-update.timer is enabled globally"
        if systemctl --global is-enabled --quiet flatpak-user-update.timer; then
            print_status "$FLATPAK_USER_UPDATE_TIMER_TEST_STRING" "$STATUS_SUCCESS"
        else
            print_status "$FLATPAK_USER_UPDATE_TIMER_TEST_STRING" "$STATUS_FAILURE"
            suggestions+="flatpak-user-update.timer is not enabled globally	To enable, run:	$ run0 systemctl enable --global flatpak-user-update.timer"
        fi

        FLATPAK_SYSTEM_UPDATE_TIMER_TEST_STRING="Ensuring flatpak-system-update.timer is enabled"
        if systemctl is-enabled --quiet flatpak-system-update.timer; then
            print_status "$FLATPAK_SYSTEM_UPDATE_TIMER_TEST_STRING" "$STATUS_SUCCESS"
        else
            print_status "$FLATPAK_SYSTEM_UPDATE_TIMER_TEST_STRING" "$STATUS_FAILURE"
            suggestions+="flatpak-system-update.timer is not enabled globally	To enable, run:	$ systemctl enable --now flatpak-system-update.timer"
        fi
    fi

    BASH_TEST_STRING="Ensuring bash environment lockdown"
    BASH_ENV_FILES=(~/.bashrc ~/.bash_profile)
    all_locked=1

    for file in "${BASH_ENV_FILES[@]}"; do
        if [ -f "$file" ]; then
            if lsattr "$file" 2>/dev/null | awk '{print $1}' | grep -q 'i'; then
                continue
            else
                all_locked=0
                break
            fi
        else
            all_locked=0
            break
        fi
    done

    if [ "$all_locked" -eq 1 ]; then
        print_status "$BASH_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$BASH_TEST_STRING" "$STATUS_FAILURE"
        suggestions+="The bash environment is not locked down	Run:	$ ujust toggle-bash-environment-lockdown"
    fi

    WHEEL_TEST_STRING="Ensuring user is not a member of wheel"
    if groups | grep -q "\bwheel\b"; then
        print_status "$WHEEL_TEST_STRING" "$STATUS_FAILURE"
    else
        print_status "$WHEEL_TEST_STRING" "$STATUS_SUCCESS"
    fi

    GNOME_XWAYLAND_TEST_STRING="Ensuring xwayland is disabled for GNOME"
    if [ -f "/etc/systemd/user/org.gnome.Shell@wayland.service.d/override.conf" ]; then
        print_status "$GNOME_XWAYLAND_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$GNOME_XWAYLAND_TEST_STRING" "$STATUS_FAILURE"
    fi

    PLASMA_XWAYLAND_TEST_STRING="Ensuring xwayland is disabled for KDE Plasma"
    if [ -f "/etc/systemd/user/plasma-kwin_wayland.service.d/override.conf" ]; then
        print_status "$PLASMA_XWAYLAND_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$PLASMA_XWAYLAND_TEST_STRING" "$STATUS_FAILURE"
    fi

    SWAY_XWAYLAND_TEST_STRING="Ensuring xwayland is disabled for Sway"
    if [ -f "/etc/sway/config.d/99-noxwayland.conf" ]; then
        print_status "$SWAY_XWAYLAND_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$SWAY_XWAYLAND_TEST_STRING" "$STATUS_FAILURE"
    fi

    EXTENSIONS_TEST_STRING="Ensuring GNOME user extensions are disabled"
    if command -v gnome-shell &> /dev/null; then
        if [ "$(gsettings get org.gnome.shell allow-extension-installation)" = "false" ]; then
            print_status "$EXTENSIONS_TEST_STRING" "$STATUS_SUCCESS"
        else
            print_status "$EXTENSIONS_TEST_STRING" "$STATUS_FAILURE"
        fi
    fi

    SELINUX_TEST_STRING="Ensuring SELinux is in Enforcing mode"
    if [ "$(getenforce)" = "Enforcing" ]; then
        print_status "$SELINUX_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$SELINUX_TEST_STRING" "$STATUS_FAILURE"
    fi

    ENVIRONMENT_TEST_STRING="Ensuring no environment file overrides"
    if diff /usr/etc/environment /etc/environment > /dev/null; then
        print_status "$ENVIRONMENT_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$ENVIRONMENT_TEST_STRING" "$STATUS_WARNING"
    fi

    GHNS_TEST_STRING="Ensuring KDE GHNS is disabled"
    KDE_GLOBALS_FILE="/etc/xdg/kdeglobals"
    if test -e $KDE_GLOBALS_FILE; then
        GHNS_STRING="$(grep 'ghns=false' $KDE_GLOBALS_FILE)"
        if [[ $GHNS_STRING == "ghns=false" ]]; then
            print_status "$GHNS_TEST_STRING" "$STATUS_SUCCESS"
        else
            print_status "$GHNS_TEST_STRING" "$STATUS_FAILURE"
        fi
    fi

    HARDENED_MALLOC_TEST_STRING="Ensuring hardened_malloc is set in ld.so.preload"
    if diff /usr/etc/ld.so.preload /etc/ld.so.preload > /dev/null; then
        print_status "$HARDENED_MALLOC_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$HARDENED_MALLOC_TEST_STRING" "$STATUS_FAILURE"
    fi

    SECUREBOOT_TEST_STRING="Ensuring secure boot is enabled"
    if [ "$(mokutil --sb-state)" == "SecureBoot enabled" ]; then
        print_status "$SECUREBOOT_TEST_STRING" "$STATUS_SUCCESS"
    else
        print_status "$SECUREBOOT_TEST_STRING" "$STATUS_FAILURE"
    fi

    if command -v flatpak &> /dev/null; then
        remotes="$(flatpak remotes -d)"
        while read -r remote ; do
            ref="$(cut -f 1 <<<"$remote")"
            url="$(cut -f 3 <<< "$remote")"
            subset="$(cut -f 5 <<< "$remote")"
            remote_string="Auditing flatpak remote $ref"
            if [[ "$url" != "https://dl.flathub.org/repo/" && "$url" != "https://dl.flathub.org/beta-repo/" ]]; then
                print_status "$remote_string" "$STATUS_FAILURE"
                echo "> $ref is configured with an unknown url!"
            elif [ "$subset" != "verified" ]; then
                print_status "$remote_string" "$STATUS_FAILURE"
                echo "> $ref is not a verified repo!"
            else
                print_status "$remote_string" "$STATUS_SUCCESS"
            fi
        done <<< "$remotes"

        declare -A flatpaks
        while read -r ref version; do
            flatpaks+=(["${ref}"]="${ref}//${version}")
        done < <(flatpak list | sort -k 1 | cut --fields 2,4)

        for f in ${!flatpaks[@]}; do
            warnings=()
            status="$STATUS_SUCCESS"
            fullref=${flatpaks["$f"]}
            permissions=$(flatpak info --show-permissions "$fullref")

            if hasPermission "$permissions" "shared" "network"; then
                [[ "$status" != "$STATUS_FAILURE" ]] && status="$STATUS_WARNING"
                warnings+=("> $f has network access!")
                suggestions+=("$f has network access	To remove it use Flatseal or run:	\$ flatpak override -u --unshare=network $f")
            fi
            if hasPermission "$permissions" "sockets" "x11" && ! hasPermission "$permissions" "sockets" "fallback-x11"; then
                status="$STATUS_FAILURE"
                warnings+=("> $f has x11 access!")
                suggestions+=("$f has x11 access	To remove it use Flatseal or run:	\$ flatpak override -u --nosocket=x11 $f")
            fi
            if hasPermission "$permissions" "sockets" "session-bus"; then
                [[ "$status" != "$STATUS_FAILURE" ]] && status="$STATUS_WARNING"
                warnings+=("> $f has access to the D-Bus session bus!")
                suggestions+=("$f has access to the D-Bus session bus	To remove it use Flatseal or run:	\$ flatpak override -u --nosocket=session-bus $f")
            fi
            if hasPermission "$permissions" "sockets" "system-bus"; then
                [[ "$status" != "$STATUS_FAILURE" ]] && status="$STATUS_WARNING"
                warnings+=("> $f has access to the D-Bus system bus!")
                suggestions+=("$f has access to the D-Bus system bus	To remove it use Flatseal or run:	\$ flatpak override -u --nosocket=system-bus $f")
            fi
            if ! hasPermission "$permissions" "LD_PRELOAD" .*"/libhardened_malloc.so"; then
                status="$STATUS_FAILURE"
                warnings+=("> $f is not requesting hardened_malloc!")
                suggestions+=("$f is not requesting hardened_malloc!	To enable it run:	\$ ujust harden-flatpak $f")
            fi
            if ! hasPermission "$permissions" "filesystems" "host-os:ro"; then
                status="$STATUS_FAILURE"
                warnings+=("> $f is missing host-os:ro permission!")
                suggestions+=("$f is missing host-os:ro permission!	This is required to load hardened_malloc.	To add it use Flatseal or run:	\$ flatpak override -u --filesystem=host-os:ro $f")
            fi
            if [[ "$bluetooth_loaded" == "true" ]] && hasPermission "$permissions" "features" "bluetooth"; then
                status="$STATUS_FAILURE"
                warnings+=("> $f has bluetooth access!")
                suggestions+=("$f has bluetooth access	To remove it use Flatseal or run:	\$ flatpak override -u --disallow=bluetooth $f")
            fi
            if [[ "$ptrace_allowed" == "true" ]] && hasPermission "$permissions" "features" "devel"; then
                status="$STATUS_FAILURE"
                warnings+=("> $f has ptrace access!")
                suggestions+=("$f has ptrace access	To remove it use Flatseal or run:	\$ flatpak override -u --disallow=devel $f")
            fi
            if hasPermission "$permissions" "shared" "ipc"; then
                status="$STATUS_FAILURE"
                warnings+=("> $f has inter-process communications access!")
                suggestions+=("$f has inter-process communications access	To remove it use Flatseal or run:	\$ flatpak override -u --unshare=ipc $f")
            fi
            if hasPermission "$permissions" "devices" "all"; then
                [[ "$status" != "$STATUS_FAILURE" ]] && status="$STATUS_WARNING"
                warnings+=("> $f has device=all permission!")
                suggestions+=("$f has device=all permission	This grants access to input devices, GPUs, raw USB, and virtualization	This may also be used as a sandbox escape vector	To remove it use Flatseal or run:	\$ flatpak override -u --nodevice=all $f	If GPU access is required, use device=dri instead	\$ flatpak override -u --device=dri $f")
            fi
            flatpak_test_string="Auditing $f"
            print_status "$flatpak_test_string" "$status"
            for warning in "${warnings[@]}"; do
                echo "$warning"
            done
        done

        print_heading Recommendations
        for suggestion in "${suggestions[@]}"; do
            readarray -t -d '	' list < <(printf "$suggestion")
            echo "${list[0]}"
            for (( i=1; i < ${#list[@]}; i++ )); do
                if [[ ${list[i]} =~ ^"$" ]]; then
                    if [[ $HAS_GUM == true ]]; then 
                        gum style --bold "  ${list[i]}"
                    else
                        echo "  ${list[i]}"
                    fi
                else
                    echo -e "  ${list[i]}"
                fi
            done
            echo
        done
    fi
