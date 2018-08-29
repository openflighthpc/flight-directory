#!/usr/bin/env bats

DIRECTORY_CLI=bin/starter
DIRECTORY_DIR=/opt/directory

delete_butlers_group() {
  ipa hostgroup-del butlers --continue
}

delete_host() {
    local name
    name="$1"

    ipa host-del "$name" --updatedns --continue  
}

cleanup() {
    delete_butlers_group
    delete_host jeeves
    delete_host alfred
}

setup() {
    source /opt/directory/etc/config && echo "$IPAPASSWORD" | kinit admin

    touch "$DIRECTORY_DIR/record"
    mv "$DIRECTORY_DIR/record"{,.bak}

    touch "$DIRECTORY_DIR/log.csv"
    mv "$DIRECTORY_DIR/log.csv"{,.bak}

    domain_info="$(ipa realmdomains-show --raw)"
    DOMAIN="$(get_domain_field "$domain_info" 'associateddomain')"

    # Ensure test data does not exist.
    cleanup
}

@test '`directory hostgroup list` lists hostgroups in a table' {
    local output

    create_butlers_group

    output="$("$DIRECTORY_CLI" hostgroup list)"
    echo "$output" | grep 'butlers.*Meeting_your_every_need'
}

@test '`directory hostgroup create` creates hostgroup with given parameters' {
    local group_info name description

    "$DIRECTORY_CLI" hostgroup create butlers --desc "Meeting_your_every_need"

    group_info="$(ipa hostgroup-find butlers --raw)"
    name="$(get_group_field "$group_info" 'cn')"
    description="$(get_group_field "$group_info" 'description')"

    [ "$name" = butlers ]
    [ "$description" =  Meeting_your_every_need ]
}

@test '`directory hostgroup modify` modifies a hostgroup with given parameters' {
    local group_info name description 

    create_butlers_group

    "$DIRECTORY_CLI" hostgroup modify butlers --desc "Gone_a_tad_rogue"

    group_info="$(ipa hostgroup-find butlers --raw)"
    description="$(get_group_field "$group_info" 'description')"

    [ "$description" = Gone_a_tad_rogue ]
}

@test '`directory hostgroup delete` deletes a given hostgroup' {
    create_butlers_group

    "$DIRECTORY_CLI" hostgroup delete butlers
    
    run ipa hostgroup-find --hostgroup-name=butlers

    [ ! "$status" -eq 0 ]
}

@test '`directory hostgroup add-member` adds given host(s) to a hostgroup' {
    local group_info 

    create_butlers_group
    create_jeeves_host
    create_alfred_host

    "$DIRECTORY_CLI" hostgroup add-member butlers jeeves alfred

    group_info="$(ipa hostgroup-find butlers --raw --all)"
    echo "$group_info" | grep 'member: fqdn=jeeves.'
    echo "$group_info" | grep 'member: fqdn=alfred.'
}

@test '`directory hostgroup remove-member` removes given host(s) from a hostgroup' {
    local group_info 
   
    create_butlers_group
    create_jeeves_host
    create_alfred_host
    ipa hostgroup-add-member butlers --hosts={jeeves,alfred}

    "$DIRECTORY_CLI" hostgroup remove-member butlers jeeves

    group_info="$(ipa hostgroup-find butlers --raw --all)"
    echo "$group_info" | grep 'member: fqdn=jeeves' | [ $(wc -l) -eq 0 ]
    echo "$group_info" | grep 'member: fqdn=alfred'
}

teardown() {
    cleanup

    mv "$DIRECTORY_DIR/record"{.bak,}
    mv "$DIRECTORY_DIR/log.csv"{.bak,}
}

create_butlers_group() {
    ipa hostgroup-add butlers --desc "Meeting_your_every_need"
}

get_group_field() {
    local raw_group_info raw_field_name
    raw_group_info="$1"
    raw_field_name="$2"
    echo "$raw_group_info" | grep "${raw_field_name}:" | xargs | cut -d ' ' -f 2
}

get_domain_field() {
    loca raw_domain_info raw_field_name fields_to_get
    raw_domain_info="$1"
    raw_field_name="$2"
    fields_to_get="${3:-2}"
    echo "$raw_domain_info" | grep "${raw_field_name}:" | xargs | cut -d ' ' -f "$fields_to_get"
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

