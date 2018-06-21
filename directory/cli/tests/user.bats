#!/usr/bin/env bats

DIRECTORY_CLI=bin/starter
DIRECTORY_DIR=/opt/directory

delete_user() {
  local login
  login="$1"

  ipa user-del "$login" --continue
}

cleanup() {
  delete_user fred
  delete_user barney
}

setup() {
  source /opt/directory/etc/config && echo "$IPAPASSWORD" | kinit admin

  touch "$DIRECTORY_DIR/record"
  mv "$DIRECTORY_DIR/record"{,.bak}

  # Ensure test users do not exist.
  cleanup
}

@test '`directory user list` lists all users in a table' {
  local output

  create_fred_user
  create_barney_user

  output="$("$DIRECTORY_CLI" user list)"
  echo "$output" | grep 'fred.*Fred Flintstone'
  echo "$output" | grep 'barney.*Barney Rubble'
}

@test '`directory user create` creates user with given parameters' {
  local user_info first last

  "$DIRECTORY_CLI" user create fred --first Fred --last Flintstone

  user_info="$(ipa user-find fred --raw)"
  first="$(get_user_field "$user_info" 'givenname')"
  last="$(get_user_field "$user_info" 'sn')"

  [ "$first" =  Fred ]
  [ "$last" =  Flintstone ]
}

@test '`directory user modify` modifies user using given parameters' {
  local user_info first last full_name display_name

  create_fred_user

  "$DIRECTORY_CLI" user modify fred --first Barney --last Rubble

  user_info="$(ipa user-find fred --raw --all)"
  first="$(get_user_field "$user_info" 'givenname')"
  last="$(get_user_field "$user_info" 'sn')"
  full_name="$(get_user_field "$user_info" 'cn' '2,3')"
  display_name="$(get_user_field "$user_info" 'displayName' '2,3')"

  [ "$first" =  Barney ]
  [ "$last" =  Rubble ]

  # `ipa user-mod` will not update these after creation when changing the first
  # and last name, but we want to for consistency.
  [ "$full_name" =  'Barney Rubble' ]
  [ "$display_name" =  'Barney Rubble' ]
}

@test '`directory user delete` deletes given user' {
  create_fred_user

  "$DIRECTORY_CLI" user delete fred

  run ipa user-find --login=fred
  [ ! "$status" -eq 0 ]
}

teardown() {
  cleanup
  mv "$DIRECTORY_DIR/record"{.bak,}
}

get_user_field() {
  local raw_user_info raw_field_name fields_to_get
  raw_user_info="$1"
  raw_field_name="$2"
  fields_to_get="${3:-2}"
  echo "$raw_user_info" | grep "${raw_field_name}:" | xargs | cut -d ' ' -f "$fields_to_get"
}

create_fred_user() {
  create_user fred Fred Flintstone
}

create_barney_user() {
  create_user barney Barney Rubble
}

create_user() {
  local login first last

  login="$1"
  first="$2"
  last="$3"

  ipa user-add "$login" --first "$first" --last "$last"
}
