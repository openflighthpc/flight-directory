#!/bin/bash
#==============================================================================
# Copyright (C) 2019-present Alces Flight Ltd.
#
# This file is part of Flight Directory.
#
# This program and the accompanying materials are made available under
# the terms of the Eclipse Public License 2.0 which is available at
# <https://www.eclipse.org/legal/epl-2.0>, or alternative license
# terms made available by Alces Flight Ltd - please direct inquiries
# about licensing to licensing@alces-flight.com.
#
# Flight Directory is distributed in the hope that it will be useful, but
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR
# IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR CONDITIONS
# OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
# PARTICULAR PURPOSE. See the Eclipse Public License 2.0 for more
# details.
#
# You should have received a copy of the Eclipse Public License 2.0
# along with Flight Directory. If not, see:
#
#  https://opensource.org/licenses/EPL-2.0
#
# For more information on Flight Directory, please visit:
# https://github.com/openflighthpc/flight-directory
#==============================================================================
# vim: set filetype=sh :

network_get_route_iface() {
    local target_ip
    target_ip="$1"

    ip -o route get "${target_ip}" \
        | head -n 1 \
        | sed 's/.*dev \(\S*\).*/\1/g'
}

network_get_iface_address() {
    local target_iface
    target_iface="$1"

    ip -o -4 address show dev ${target_iface} \
        | head -n 1 \
        | sed 's/.*inet \(\S*\)\/.*/\1/g'
}

_setup() {
    local dots
    DIRECTORYIP="_DIRECTORYIP_"
    CLIENTNAME=$(hostname -s)
    CLIENTIP=$(network_get_iface_address $(network_get_route_iface ${DIRECTORYIP}))
    dots=$(hostname -d | grep -o "\." | wc -l)
    if [ "$dots" == "2" ]; then
        DOMAIN=$(hostname -d)
    elif [ "$dots" == "3" ]; then
        DOMAIN=$(hostname -d | cut -d . -f 2-4)
        CLUSTER=$(hostname -d | cut -d . -f 1)
    fi
    DIRECTORYFQDN="directory.$DOMAIN"
    REALM=$(echo $DOMAIN | sed -e 's/\(.*\)/\U\1/')
    ONETIMEPASS=$(openssl rand -hex 6)
}

_enrol_ipa() {
    gw_intf=$(network_get_route_iface 8.8.8.8)
    # Stop DHCP changing /etc/resolv.conf on reboot
    if grep -q "^PEERDNS" /etc/sysconfig/network-scripts/ifcfg-$gw_intf; then
        sed -i -e "s/^PEERDNS.*$/PEERDNS=\"no\"/g" \
            /etc/sysconfig/network-scripts/ifcfg-$gw_intf
    else
        cat <<EOF >>/etc/sysconfig/network-scripts/ifcfg-$gw_intf
PEERDNS="no"
EOF
    fi

    # Prepare /etc/resolv.conf
    if [ -z $CLUSTER ]; then
        echo -e "search $DOMAIN\nnameserver ${DIRECTORYIP}" > /etc/resolv.conf
    else
        echo -e "search $CLUSTER.$DOMAIN $DOMAIN\nnameserver ${DIRECTORYIP}" > /etc/resolv.conf
    fi

    # Install required packages
    if yum -y -e0 install ipa-client ipa-admintools; then
        # Sign up to IPA
        if ipa-client-install \
               --no-ntp \
               --mkhomedir \
               --force-join \
               --ssh-trust-dns \
               --realm="$REALM" \
               --server="${DIRECTORYFQDN}" \
               -w "$ONETIMEPASS" \
               --domain="`hostname -d`" \
               --unattended; then
            systemctl restart dbus
            # https://major.io/2015/07/27/very-slow-ssh-logins-on-fedora-22/
            systemctl restart systemd-logind
        else
            return 1
        fi
    else
        return 1
    fi
}

_trigger_add() {
    export cw_FLIGHT_TRIGGER_auth=_TRIGGERAUTH_
    "${_TRIGGER}" https://${DIRECTORYIP}:8444/trigger/add \
                  $CLIENTNAME $CLIENTIP $ONETIMEPASS $CLUSTER |
        "${_JQ}" -r '.responses[].result'
}

main() {
    if [ -d "${cw_ROOT}"/etc/config/domain-directory ]; then
        echo "This node has already been subscribed to Flight Directory."
        exit 0
    fi
    local res
    _setup
    res=$(_trigger_add)

    if [ "$res" == "OK" ]; then
        echo "Addition of '$CLIENTNAME' to Flight Directory succeeded."
        if _enrol_ipa; then
            mkdir -p "${cw_ROOT}"/etc/config/domain-directory
        else
            echo "IPA enrolment failed; retry manually with OTP: $ONETIMEPASS"
        fi
    else
        echo "Unable to add node '$CLIENTNAME' to Flight Directory: ${res}"
    fi
}

_JQ="${cw_ROOT}"/opt/jq/bin/jq
_TRIGGER="${cw_ROOT}"/libexec/share/flight-trigger

main "$@"
