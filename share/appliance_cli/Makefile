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

.PHONY: unit-test functional-test test setup development-setup rsync \
	watch-rsync remote-run remote-add-dependency ipython

REMOTE_DIR='/tmp/cli'

unit-test:
	. venv/bin/activate && pytest src/ --ignore=src/nagios_interface/venv

functional-test:
	. venv/bin/activate && bats --pretty tests/

test: unit-test functional-test

setup:
	bin/setup

development-setup: setup
	bin/development-setup

rsync:
	rsync -r --copy-links --perms . root@${IP}:${REMOTE_DIR}

watch-rsync:
	rerun \
		--name 'Flight Appliance CLI' \
		--pattern '**/*' \
		--exit \
		make rsync IP=${IP}

# Note: need to become root to run ipa commands; -t option allows coloured
# output.
remote-run: rsync
	ssh -t dev@${IP} "sudo su - -c \"cd ${REMOTE_DIR} && ${COMMAND}\""

remote-add-dependency:
	make remote-run IP=${IP} COMMAND='. venv/bin/activate && pip install ${DEPENDENCY} && pip freeze > requirements.txt'
	scp dev@${IP}:${REMOTE_DIR}/requirements.txt requirements.txt

ipython:
	. venv/bin/activate && ipython
