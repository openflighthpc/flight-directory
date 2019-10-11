#!/usr/bin/env bats
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

DIRECTORY_CLI=bin/starter
DIRECTORY_DIR=/opt/directory
export ADVANCED=true

setup() {
    source /opt/directory/etc/config && echo "$IPAPASSWORD" | kinit admin

    touch "$DIRECTORY_DIR/record"
    mv "$DIRECTORY_DIR/record"{,.bak}

    touch "$DIRECTORY_DIR/log.csv"
    mv "$DIRECTORY_DIR/log.csv"{,.bak}

    domain_info="$(ipa realmdomains-show --raw)"
    DOMAIN="$(get_host_field "$domain_info" 'associateddomain')"

    # Ensure test hosts do not exist.
    cleanup
}

teardown() {
    cleanup

    mv "$DIRECTORY_DIR/record"{.bak,}
    mv "$DIRECTORY_DIR/log.csv"{.bak,}
}

cleanup() {
    delete_host 'jeeves.'$DOMAIN
    delete_host 'alfred.'$DOMAIN
}

delete_host() {
    local name
    name="$1"

    ipa host-del "$name" --updatedns --continue
}

delete_reverse_record() {
    local ip
    ip="$1"

    ipa dnsrecord-del 10.10.in-addr.arpa "$ip" --del-all
}

create_jeeves_host() {
    create_host jeeves.$DOMAIN 10.10.255.254
}

create_alfred_host() {
    create_host alfred.$DOMAIN 10.10.255.255
}

create_host() {
    local host ip
    host="$1"
    ip="$2"

    ipa host-add "$host" --ip-address "$ip"
}

@test '`directory host list` lists all hosts in a table' {
    local output

    create_jeeves_host
    create_alfred_host

    output="$("$DIRECTORY_CLI" host list)"
    echo "$output" | grep 'jeeves.'
    echo "$output" | grep 'alfred.'
}

@test '`directory host create` creates a host with given parameters' {
    local host_info ip

    "$DIRECTORY_CLI" host create jeeves.$DOMAIN --ip-address 10.10.255.254

    host_info="$(ipa host-find jeeves --raw --all)"
    hostname="$(get_host_field "$host_info" 'serverHostName')"

    [ "$hostname" = jeeves ]
}

@test '`directory host modify` modifies a host ip' {
    local _info first last full_name display_name

    create_jeeves_host

    "$DIRECTORY_CLI" host modify jeeves.$DOMAIN --ip-address 10.10.255.253

    host_dns_info="$(ipa dnsrecord-find "$DOMAIN" --name=jeeves --all --raw)"
    ip="$(get_host_field "$host_dns_info" 'arecord')"

    #appears to be needed as the modify ip above stops the reverse record being deleted properly
    ipa dnsrecord-del 10.10.in-addr.arpa 254.255 --del-all

    [ "$ip" = 10.10.255.253 ]
}

@test '`directory host delete` deletes given host' {
  create_jeeves_host

  "$DIRECTORY_CLI" host delete jeeves

  run ipa user-find --'Host name'=jeeves
  [ ! "$status" -eq 0 ]
}

get_host_field() {
    local raw_host_info raw_field_name fields_to_get
    raw_host_info="$1"
    raw_field_name="$2"
    fields_to_get="${3:-2}"
    echo "$raw_host_info" | grep "${raw_field_name}:" | xargs | cut -d ' ' -f "$fields_to_get"
}
