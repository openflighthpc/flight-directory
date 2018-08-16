#!/usr/bin/env bats

DIRECTORY_CLI=bin/starter
DIRECTORY_DIR=/opt/directory

setup() {
  source /opt/directory/etc/config && echo "$IPAPASSWORD" | kinit admin

  touch "$DIRECTORY_DIR/log.csv"
  mv "$DIRECTORY_DIR/log.csv"{,.bak}

  # Ensure test hosts do not exist.
  cleanup
}

teardown() {
    cleanup
    mv "$DIRECTORY_DIR/log.csv"{,.bak}
}

cleanup() {
    delete_host Jeeves
    delete_host Alfred
}

delete_host() {
  local login

  login = "$1"

  ipa host-del "$login" --continue
}

create_host_one() {
    create_host Jeeves 1.1.1.1
}

create_host_two() {
    create_host Alfred 2.2.2.2
}

create_host() {
    local host ip

    host = "$1"
    ip = "$2"

    ipa host-add "$host" --ip-address "$ip"
}

@test '`directory host list` lists all hosts in a table' {
    local output

    create_host_one
    create_host_two

    output="$("$DIRECTORY_CLI" user list)"
    echo "$output" | grep 'Jeeves.*1.1.1.1'
    echo "$output" | grep 'Alfred.*2.2.2.2'
}

@test '`directory host create` creates a host with given parameters' {
    local host_info ip

    "$DIRECTORY_CLI" host create Jeeves --ip-address 1.1.1.1

    host_info="$(ipa host-find Jeeves --raw)"
    #come back to this
}

@test '`directory host modify` modifies a host\'s ip' {
  local _info first last full_name display_name

  create_host_one

  "$DIRECTORY_CLI"  modify Jeeves --ip-address 3.3.3.3

  host_dns_info="$(ipa dnsrecord-find *DOMAIN NAME* --name=Jeeves --all)"

}

@test '`directory host delete` deletes given host' {
  create_host_one

  "$DIRECTORY_CLI" user delete Jeeves

  run ipa user-find --'Host name'=Jeeves
  [ ! "$status" -eq 0 ]
}


















