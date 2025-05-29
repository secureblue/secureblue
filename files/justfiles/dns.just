# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

# setup system DNS resolution
dns-selector:
    #! /bin/run0 /bin/bash
    # constants
    readonly resolved_conf="/etc/systemd/resolved.conf.d/10-securedns.conf"
    readonly policy_file="/etc/trivalent/policies/managed/10-securedns-browser.json"
    mkdir -p /etc/systemd/resolved.conf.d/
    mkdir -p /etc/trivalent/policies/managed/
    # variables
    valid_input="0"
    resolver_selection=""
    resolver_subselection=""
    resolver_has_second_ip=""
    resolver_supports_ipv6=""
    resolver_dnssec=""
    resolver_ipv4_address=""
    resolver_ipv4_address_2=""
    resolver_ipv6_address=""
    resolver_ipv6_address_2=""
    resolver_hostname=""
    resolver_https_address=""
    set_browser_policy=""
    opportunistic=""
    clear_state=""

    echo "Below will be some options to set the DNS resolver for systemd-resolved."
    echo "All resolvers support DNS-over-TLS (DoT) or DNS-over-QUIC (DoQ), DNS-over-HTTPS (DoH), and DNSSEC."
    echo "Please select which DNS resolver you would like to set:"
    echo "    0) Network Default - do nothing, rely purely on the network for resolution (when using a VPN, this option is best to guarentee usage of the VPN's DNS resolver)"
    echo "    1) Opportunistic Upgrade - try to upgrade to DoT (encrypted DNS) resolution and/or DNSSEC enforcement (this configuration may break networking)"
    echo "    2) Control D - has content filtering, anycast"
    echo "    3) Mullvad - has content filtering, anycast"
    echo "    4) Cloudflare - very fast with some data collection, anycast"
    echo "    5) DNSForge - powerful filtering but can be very slow"
    echo "    6) Custom Resolver - use a custom resolver (must support DoT/DoQ, ideally also supports DNSSEC, DoH support is also required to set a browser policy should that be desired)"
    while [[ "$valid_input" == "0" ]]; do
        read -rp "Selection [0-6]: " resolver_selection
        if [[ "$resolver_selection" == [0123456]* ]]; then
            valid_input="1"
        else
            echo "That is not a valid selection."
        fi
    done
    valid_input="0"

    echo "" # blank space
    case "$resolver_selection" in
        0)
            clear_state="1"
            echo "Resetting resolved to default state."
            ;;
        1)
            clear_state="1"
            opportunistic="1"
            ;;
        2)
            resolver_has_second_ip="y"
            resolver_supports_ipv6="y"
            resolver_dnssec="y"
            echo "Setting resolver Control D."
            echo "What content would you like to filter:"
            echo "    0) No filtering"
            echo "    1) Malware: Malware filtering"
            echo "    2) Standard: Malware + ad and tracker filtering"
            echo "    3) Social: Standard + social media filtering"
            echo "    4) Family: Social + adult content filtering (also enables safe search in major search engines)"
            while [[ "$valid_input" == "0" ]]; do
                read -rp "Selection [0-4]: " resolver_subselection
                if [[ "$resolver_subselection" == [01234]* ]]; then
                    valid_input="1"
                else
                    echo "That is not a valid selection."
                fi
            done
            valid_input="0"
            case "$resolver_subselection" in
                # Source for the IP addresses and hostnames/URLs: https://controld.com/free-dns
                0)
                    resolver_ipv4_address="76.76.2.0"
                    resolver_ipv4_address_2="76.76.10.0"
                    resolver_ipv6_address="2606:1a40::"
                    resolver_ipv6_address_2="2606:1a40:1::"
                    resolver_hostname="p0.freedns.controld.com"
                    resolver_https_address="https://freedns.controld.com/p0"
                    ;;
                1)
                    resolver_ipv4_address="76.76.2.1"
                    resolver_ipv4_address_2="76.76.10.1"
                    resolver_ipv6_address="2606:1a40::1"
                    resolver_ipv6_address_2="2606:1a40:1::1"
                    resolver_hostname="p1.freedns.controld.com"
                    resolver_https_address="https://freedns.controld.com/p1"
                    ;;
                2)
                    resolver_ipv4_address="76.76.2.2"
                    resolver_ipv4_address_2="76.76.10.2"
                    resolver_ipv6_address="2606:1a40::2"
                    resolver_ipv6_address_2="2606:1a40:1::2"
                    resolver_hostname="p2.freedns.controld.com"
                    resolver_https_address="https://freedns.controld.com/p2"
                    ;;
                3)
                    resolver_ipv4_address="76.76.2.3"
                    resolver_ipv4_address_2="76.76.10.3"
                    resolver_ipv6_address="2606:1a40::3"
                    resolver_ipv6_address_2="2606:1a40:1::3"
                    resolver_hostname="p3.freedns.controld.com"
                    resolver_https_address="https://freedns.controld.com/p3"
                    ;;
                4)
                    resolver_ipv4_address="76.76.2.4"
                    resolver_ipv4_address_2="76.76.10.4"
                    resolver_ipv6_address="2606:1a40::4"
                    resolver_ipv6_address_2="2606:1a40:1::4"
                    resolver_hostname="family.freedns.controld.com"
                    resolver_https_address="https://freedns.controld.com/family"
                    ;;
            esac
            ;;
        3)
            resolver_has_second_ip="n"
            resolver_supports_ipv6="y"
            resolver_dnssec="y"
            echo "Setting resolver Mullvad."
            echo "What content would you like to filter:"
            echo "    0) No filtering"
            echo "    1) Standard: Ad and tracker filtering"
            echo "    2) Base: Standard + malware filtering"
            echo "    3) Extended: Base + social media filtering"
            echo "    4) Family: Base + gambling and adult content filtering"
            echo "    5) All: Family + social media filtering"
            while [[ "$valid_input" == "0" ]]; do
                read -rp "Selection [0-5]: " resolver_subselection
                if [[ "$resolver_subselection" == [012345]* ]]; then
                    valid_input="1"
                else
                    echo "That is not a valid selection."
                fi
            done
            valid_input="0"
            case "$resolver_subselection" in
                # Source for the IP addresses and hostnames/URLs: https://mullvad.net/en/help/dns-over-https-and-dns-over-tls
                0)
                    resolver_ipv4_address="194.242.2.2"
                    resolver_ipv6_address="2a07:e340::2"
                    resolver_hostname="dns.mullvad.net"
                    ;;
                1)
                    resolver_ipv4_address="194.242.2.3"
                    resolver_ipv6_address="2a07:e340::3"
                    resolver_hostname="adblock.dns.mullvad.net"
                    ;;
                2)
                    resolver_ipv4_address="194.242.2.4"
                    resolver_ipv6_address="2a07:e340::4"
                    resolver_hostname="base.dns.mullvad.net"
                    ;;
                3)
                    resolver_ipv4_address="194.242.2.5"
                    resolver_ipv6_address="2a07:e340::5"
                    resolver_hostname="extended.dns.mullvad.net"
                    ;;
                4)
                    resolver_ipv4_address="194.242.2.6"
                    resolver_ipv6_address="2a07:e340::6"
                    resolver_hostname="family.dns.mullvad.net"
                    ;;
                5)
                    resolver_ipv4_address="194.242.2.9"
                    resolver_ipv6_address="2a07:e340::9"
                    resolver_hostname="all.dns.mullvad.net"
                    ;;
            esac
            resolver_https_address="https://$resolver_hostname/dns-query"
            ;;
        4)
            resolver_has_second_ip="y"
            resolver_supports_ipv6="y"
            resolver_dnssec="y"
            echo "Setting resolver Cloudflare. (glory to the cloud)"
            echo "What content would you like to filter:"
            echo "    0) No filtering"
            echo "    1) Security: Malware filtering"
            echo "    2) Family: Security + adult content filtering"
            while [[ "$valid_input" == "0" ]]; do
                read -rp "Selection [0-2]: " resolver_subselection
                if [[ "$resolver_subselection" == [012]* ]]; then
                    valid_input="1"
                else
                    echo "That is not a valid selection."
                fi
            done
            valid_input="0"
            case "$resolver_subselection" in
                # Source for the IP addresses and hostnames/URLs: https://developers.cloudflare.com/1.1.1.1/infrastructure/network-operators/#available-endpoints
                0)
                    resolver_ipv4_address="1.1.1.1"
                    resolver_ipv4_address_2="1.0.0.1"
                    resolver_ipv6_address="2606:4700:4700::1111"
                    resolver_ipv6_address_2="2606:4700:4700::1001"
                    resolver_hostname="cloudflare-dns.com"
                    ;;
                1)
                    resolver_ipv4_address="1.1.1.2"
                    resolver_ipv4_address_2="1.0.0.2"
                    resolver_ipv6_address="2606:4700:4700::1112"
                    resolver_ipv6_address_2="2606:4700:4700::1002"
                    resolver_hostname="security.cloudflare-dns.com"
                    ;;
                2)
                    resolver_ipv4_address="1.1.1.3"
                    resolver_ipv4_address_2="1.0.0.3"
                    resolver_ipv6_address="2606:4700:4700::1113"
                    resolver_ipv6_address_2="2606:4700:4700::1003"
                    resolver_hostname="family.cloudflare-dns.com"
                    ;;
            esac
            resolver_https_address="https://$resolver_hostname/dns-query"
            ;;
        5)
            resolver_has_second_ip="y"
            resolver_supports_ipv6="y"
            resolver_dnssec="y"
            echo "Setting resolver DNSForge."
            echo "What content would you like to filter:"
            echo "    0) Standard: Ad, tracker, and malware filtering"
            echo "    1) Clean: Standard + adult content filtering"
            echo "    2) Hard: Clean + stricter ad, tracker, and malware filtering"
            while [[ "$valid_input" == "0" ]]; do
                read -rp "Selection [0-2]: " resolver_subselection
                if [[ "$resolver_subselection" == [012]* ]]; then
                    valid_input="1"
                else
                    echo "That is not a valid selection."
                fi
            done
            valid_input="0"
            case "$resolver_subselection" in
                # Source for the IP addresses and hostnames/URLs: https://dnsforge.de/#dnsdaten
                0)
                    resolver_ipv4_address="176.9.93.198"
                    resolver_ipv4_address_2="176.9.1.117"
                    resolver_ipv6_address="2a01:4f8:151:34aa::198"
                    resolver_ipv6_address_2="2a01:4f8:141:316d::117"
                    resolver_hostname="dnsforge.de"
                    ;;
                1)
                    resolver_ipv4_address="49.12.223.2"
                    resolver_ipv4_address_2="49.12.43.208"
                    resolver_ipv6_address="2a01:4f8:c17:4fbc::2"
                    resolver_ipv6_address_2="2a01:4f8:c012:ed89::208"
                    resolver_hostname="clean.dnsforge.de"
                    ;;
                2)
                    resolver_ipv4_address="49.12.222.213"
                    resolver_ipv4_address_2="88.198.122.154"
                    resolver_ipv6_address="2a01:4f8:c17:2c61::213"
                    resolver_ipv6_address_2="2a01:4f8:c013:5ec0::154"
                    resolver_hostname="hard.dnsforge.de"
                    ;;
            esac
            resolver_https_address="https://$resolver_hostname/dns-query"
            ;;
        6)
            echo "Setting custom resolver."
            echo "NOTE: If the resolver does not support DoT/DoQ or DNSSEC, this process will not work."
            echo ""
            echo "Please provide the technical information."
            read -rp "Please enter the resolver's IPv4 address (e.g. '1.1.1.2'): " resolver_ipv4_address
            read -rp "Does the resolver provide two distinct IPv4 addresses (e.g. '1.1.1.2' and '1.0.0.2')? [Y/n] " resolver_has_second_ip
            resolver_has_second_ip=${resolver_has_second_ip:-y}
            if [[ "$resolver_has_second_ip" == [Yy]* ]]; then
                read -rp "Please enter the resolver's second IPv4 address: " resolver_ipv4_address_2
            fi
            read -rp "Does the resolver support IPv6 (e.g. '2606:4700:4700::1112')? [Y/n] " resolver_supports_ipv6
            resolver_supports_ipv6=${resolver_supports_ipv6:-y}
            if [[ "$resolver_supports_ipv6" == [Yy]* ]]; then
                read -rp "Please enter the resolver's IPv6 address: " resolver_ipv6_address
                if [[ "$resolver_has_second_ip" == [Yy]* ]]; then
                    read -rp "Please enter the resolver's second IPv6 address: " resolver_ipv6_address_2
                fi
            fi
            read -rp "Please enter the second resolver's hostname (e.g. 'security.cloudflare-dns.com'): " resolver_hostname
            read -rp "Do you want to enable DNSSEC (this can cause networking issues notably in virtual machines, it is recommended if you do not suffer issues)? [Y/n] " resolver_dnssec
            resolver_dnssec=${resolver_dnssec:-y}
            ;;
    esac

    if [[ "$clear_state" == "1" ]]; then
        if [[ -f "$policy_file" ]]; then
            rm $policy_file
            echo "Removed browser policy."
        fi
    fi

    if [[ "$opportunistic" == "1" ]]; then
        cat << EOF > "$resolved_conf"
    [Resolve]
    DNSOverTLS=opportunistic
    DNSSEC=allow-downgrade
    EOF
    elif [[ "$clear_state" == "1" ]]; then
        if [[ -f "$resolved_conf" ]]; then
            rm $resolved_conf
        fi
        echo "Configuration file for resolved removed."
    else
        read -rp "Would you like the resolver to be set in the default browser (Trivalent) via management policy? [y/N] " set_browser_policy
        if [[ "$set_browser_policy" == [Yy]* && "$resolver_selection" == 6 ]]; then
            read -rp "Please enter the second resolver's HTTPS address (e.g. 'https://security.cloudflare-dns.com/dns-query'): " resolver_https_address
        fi

        resolved_conf_dns_string=""
        resolved_conf_dns_string+="DNS="
        resolved_conf_dns_string+=" $resolver_ipv4_address"
        resolved_conf_dns_string+="#$resolver_hostname"
        if [[ "$resolver_has_second_ip" == [Yy]* ]]; then
            resolved_conf_dns_string+=" $resolver_ipv4_address_2"
            resolved_conf_dns_string+="#$resolver_hostname"
        fi
        if [[ "$resolver_supports_ipv6" == [Yy]* ]]; then
            resolved_conf_dns_string+=" $resolver_ipv6_address"
            resolved_conf_dns_string+="#$resolver_hostname"
            if [[ "$resolver_has_second_ip" == [Yy]* ]]; then
                resolved_conf_dns_string+=" $resolver_ipv6_address_2"
                resolved_conf_dns_string+="#$resolver_hostname"
            fi
        fi

        resolved_conf_dnssec_string=""
        if [[ "$resolver_dnssec" == [Yy]* ]]; then
            resolved_conf_dnssec_string+="DNSSEC=true"
        fi

        cat << EOF > "$resolved_conf"
    [Resolve]
    DNSOverTLS=true
    $resolved_conf_dns_string
    $resolved_conf_dnssec_string
    EOF
    fi

    if [[ -f "$resolved_conf" ]]; then
        chmod 644 "$resolved_conf"
    fi

    systemctl restart systemd-resolved

    echo "Configation for resolved set and service restarted."

    if [[ "$set_browser_policy" != [Yy]* ]]; then
        exit 0
    fi
    cat << EOF > "$policy_file"
    {
        "DnsOverHttpsMode": "secure",
        "DnsOverHttpsTemplates": "$resolver_https_address"
    }
    EOF
    chmod 644 "$policy_file"

    echo "Browser policy set with selected resolver."
