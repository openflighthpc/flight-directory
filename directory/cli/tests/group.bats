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

delete_flintstones_group() {
  ipa group-del flintstones --continue
}

delete_user() {
  local login
  login="$1"

  ipa user-del "$login" --continue
}

cleanup() {
  delete_flintstones_group
  delete_user fred
  delete_user barney
}

setup() {
  source /opt/directory/etc/config && echo "$IPAPASSWORD" | kinit admin

  touch "$DIRECTORY_DIR/record"
  mv "$DIRECTORY_DIR/record"{,.bak}

  touch "$DIRECTORY_DIR/log.csv"
  mv "$DIRECTORY_DIR/log.csv"{,.bak}

  # Ensure test data does not exist.
  cleanup
}

@test '`directory group list` lists all groups with members in a table' {
  local output

  create_flintstones_group
  create_fred_user
  create_barney_user
  ipa group-add-member flintstones --users={fred,barney}

  output="$("$DIRECTORY_CLI" group show flintstones)"
  echo "$output" | \
    grep 'barney'
}

@test '`directory group create` creates group with given parameters' {
  local group_info name description

  "$DIRECTORY_CLI" group create flintstones --desc "Cutting_edge_stone_research"

  group_info="$(ipa group-find flintstones --raw)"
  name="$(get_group_field "$group_info" 'cn')"
  description="$(get_group_field "$group_info" 'description')"

  [ "$name" =  flintstones ]
  [ "$description" =  Cutting_edge_stone_research ]
}

@test '`directory group modify` modifies group using given parameters' {
  local group_info name description

  create_flintstones_group

  "$DIRECTORY_CLI" group modify flintstones --desc "Computational_rock_dynamics"

  group_info="$(ipa group-find flintstones --raw)"
  description="$(get_group_field "$group_info" 'description')"

  [ "$description" =  Computational_rock_dynamics ]
}

@test '`directory group delete` deletes given group' {
  create_flintstones_group

  "$DIRECTORY_CLI" group delete flintstones

  run ipa group-find --group-name=flintstones
  [ ! "$status" -eq 0 ]
}

@test '`directory group member add` adds given user(s) to group' {
  local group_info

  create_flintstones_group
  create_fred_user
  create_barney_user

  "$DIRECTORY_CLI" group member add flintstones fred barney

  group_info="$(ipa group-find flintstones --raw --all)"
  echo "$group_info" | grep 'member: uid=fred,'
  echo "$group_info" | grep 'member: uid=barney,'
}

@test '`directory group member remove` removes given user(s) from group' {
  local group_info

  create_flintstones_group
  create_fred_user
  create_barney_user
  ipa group-add-member flintstones --users={fred,barney}

  "$DIRECTORY_CLI" group member remove flintstones fred barney

  group_info="$(ipa group-find flintstones --raw --all)"
  echo "$group_info" | grep 'member: uid=fred,' | [ $(wc -l) -eq 0 ]
  echo "$group_info" | grep 'member: uid=barney,' | [ $(wc -l) -eq 0 ]
}

teardown() {
  cleanup

  mv "$DIRECTORY_DIR/record"{.bak,}
  mv "$DIRECTORY_DIR/log.csv"{.bak,}
}

create_flintstones_group() {
  ipa group-add flintstones --desc "Cutting_edge_stone_research"
}

get_group_field() {
  local raw_group_info raw_field_name
  raw_group_info="$1"
  raw_field_name="$2"
  echo "$raw_group_info" | grep "${raw_field_name}:" | xargs | cut -d ' ' -f 2
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
