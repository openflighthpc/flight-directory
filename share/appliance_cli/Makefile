
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
	rsync -r --copy-links --perms . dev@${IP}:${REMOTE_DIR}

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
