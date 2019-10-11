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

  touch "$DIRECTORY_DIR/log.csv"
  mv "$DIRECTORY_DIR/log.csv"{,.bak}

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

@test '`directory user disable` disables given user' {
  create_fred_user

  "$DIRECTORY_CLI" user disable fred

  user_info="$(ipa user-find fred --raw --all)"
  disabled="$(get_user_field "$user_info" 'nsaccountlock')"

  [ "$disabled" = TRUE ]

}

@test '`directory user enable` enables given user' {
  create_fred_user

  ipa user-disable fred
  "$DIRECTORY_CLI" user enable fred

  user_info="$(ipa user-find fred --raw --all)"
  disabled="$(get_user_field "$user_info" 'nsaccountlock')"

  [ "$disabled" = FALSE ]

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
  mv "$DIRECTORY_DIR/log.csv"{.bak,}
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
